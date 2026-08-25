import re
from PySide6.QtCore import QObject
from PySide6.QtWebEngineCore import (
    QWebEngineScript,
    QWebEngineUrlRequestInterceptor,
)
from .storage import load_wordlist, rules_path, whitelist_path
AD_DOMAINS = """
doubleclick.net
googlesyndication.com
googleadservices.com
google-analytics.com
analytics.google.com
googletagmanager.com
googletagservices.com
fundingchoicesmessages.google.com
adservice.google.com
2mdn.net
adnxs.com
adsrvr.org
rubiconproject.com
pubmatic.com
openx.net
criteo.com
criteo.net
taboola.com
outbrain.com
mgid.com
revcontent.com
zergnet.com
content-ad.net
adblade.com
zedo.com
smartadserver.com
adform.net
yieldmo.com
indexww.com
casalemedia.com
33across.com
bidswitch.net
sharethrough.com
media.net
amazon-adsystem.com
moatads.com
scorecardresearch.com
quantserve.com
quantcount.com
chartbeat.com
chartbeat.net
parsely.com
mixpanel.com
segment.com
segment.io
amplitude.com
heapanalytics.com
hotjar.com
fullstory.com
logrocket.com
logrocket.io
smartlook.com
mouseflow.com
crazyegg.com
clicktale.net
inspectlet.com
sessioncam.com
luckyorange.com
statcounter.com
histats.com
opentracker.net
newrelic.com
nr-data.net
sentry.io
branch.io
appsflyer.com
adjust.com
kochava.com
singular.net
connect.facebook.net
ads-twitter.com
ads.linkedin.com
bat.bing.com
clarity.ms
mc.yandex.ru
an.yandex.ru
adfox.ru
top-fwz1.mail.ru
counter.yadro.ru
teads.tv
yieldlab.net
improvedigital.com
adition.com
adscale.de
ligatus.com
plista.com
nuggad.net
omtrdc.net
demdex.net
everesttech.net
2o7.net
doubleverify.com
adsafeprotected.com
flashtalking.com
sizmek.com
imrworldwide.com
popads.net
popcash.net
propellerads.com
onesignal.com
pushwoosh.com
izooto.com
optimizely.com
vwo.com
abtasty.com
kissmetrics.com
snowplowanalytics.com
plausible.io
usefathom.com
posthog.com
cloudflareinsights.com
stats.wp.com
adroll.com
triplelift.com
sonobi.com
gumgum.com
undertone.com
conversantmedia.com
spotxchange.com
tapad.com
bluekai.com
krux.com
rlcdn.com
agkn.com
crwdcntrl.net
exelator.com
"""
SENSITIVE_LABELS = {
    "ads", "ad", "adservice", "adserver", "adsense", "analytics",
    "tracker", "tracking", "pixel", "beacon", "doubleclick",
}
BUILTIN_RULES = (
    "facebook.com/tr",
)
BLOCKED_PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Page unavailable</title><style>
body {{ background:#f2f2f2; color:#444; font-family:'Segoe UI',Arial,sans-serif;
display:flex; align-items:center; justify-content:center; height:100vh; margin:0; }}
.box {{ text-align:center; max-width:440px; }}
h1 {{ font-size:22px; font-weight:500; color:#333; margin:0 0 10px; }}
p {{ font-size:13px; color:#777; margin:0 0 14px; }}
code {{ font-size:11px; color:#b0b0b0; }}
</style></head><body><div class="box">
<h1>This page is unavailable</h1>
<p>It may be restricted or temporarily unreachable.</p>
<code>{code}</code>
</div></body></html>"""
COSMETIC_JS = """(function () {
    var bad = ["doubleclick", "googlesyndication", "googleadservices",
               "taboola", "outbrain", "adnxs", "criteo", "scorecardresearch",
               "pubmatic", "rubiconproject", "smartadserver", "mgid",
               "revcontent", "amazon-adsystem", "moatads"];
    function isBad(value) {
        if (!value) { return false; }
        value = value.toLowerCase();
        for (var i = 0; i < bad.length; i++) {
            if (value.indexOf(bad[i]) !== -1) { return true; }
        }
        return false;
    }
    function clean(root) {
        try {
            var media = root.querySelectorAll("iframe, img, ins");
            for (var i = 0; i < media.length; i++) {
                var node = media[i];
                var src = node.getAttribute && (node.getAttribute("src") ||
                         node.getAttribute("data-src"));
                if (isBad(src)) { node.remove(); }
            }
            var boxes = root.querySelectorAll(
                "ins.adsbygoogle, [id^='google_ads'], [id^='div-gpt-ad'], " +
                "[id^='aswift'], [id*='taboola'], [class~='taboola'], " +
                "[class~='advertisement'], [class~='ad-banner'], " +
                "[class~='ad-container'], [class~='ad-wrapper']");
            for (var j = 0; j < boxes.length; j++) { boxes[j].remove(); }
        } catch (err) { }
    }
    clean(document);
    document.addEventListener("DOMContentLoaded", function () { clean(document); });
})();"""
class RuleEngine(QObject):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.enabled = bool(settings.get("adblock", True))
        self.whitelist_only = bool(settings.get("whitelist_only", False))
        self.site_allow = set()
        self.domain_blocks = set()
        self.regex_rules = []
        self.whitelist = set()
        self.total_blocked = 0
        self.per_host = {}
        self.reload_rules()
    def reload_rules(self):
        self.domain_blocks = {
            line.strip().lower()
            for line in AD_DOMAINS.splitlines() if line.strip()
        }
        self.regex_rules = []
        for line in BUILTIN_RULES:
            self.add_rule(line)
        for line in load_wordlist(rules_path()):
            self.add_rule(line)
        self.whitelist = set(load_wordlist(whitelist_path()))
    def add_rule(self, line):
        line = line.split("$", 1)[0].strip().lower()
        if not line or line.startswith("!") or line.startswith("#"):
            return
        if line.startswith("||"):
            body = line[2:]
            for stop in ("/", "^", "*"):
                pos = body.find(stop)
                if pos != -1:
                    body = body[:pos]
            body = body.strip()
            if body:
                self.domain_blocks.add(body)
            return
        anchored_start = line.startswith("|")
        anchored_end = line.endswith("|") and len(line) > 1
        body = line[1:] if anchored_start else line
        body = body[:-1] if anchored_end else body
        pattern = re.escape(body)
        pattern = pattern.replace(r"\\*", ".*")
        pattern = pattern.replace(r"\\^", "(?:[/:?=&]|$)")
        if anchored_start:
            pattern = "^" + pattern
        if anchored_end:
            pattern = pattern + "$"
        try:
            self.regex_rules.append(re.compile(pattern))
        except re.error:
            pass
    @staticmethod
    def host_in_set(host, domains):
        for domain in domains:
            if host == domain or host.endswith("." + domain):
                return True
        return False
    def should_block(self, url, first_party):
        if not self.enabled:
            return False
        host = url.host().lower()
        if not host:
            return False
        if first_party.isValid() and self.host_in_set(first_party.host().lower(),
                                                      self.site_allow):
            return False
        if self.host_in_set(host, self.domain_blocks):
            return True
        labels = host.split(".")
        if labels and labels[0] in SENSITIVE_LABELS:
            return True
        if self.regex_rules:
            target = url.toString().lower()
            for rule in self.regex_rules:
                if rule.search(target):
                    return True
        return False
    def host_allowed(self, host):
        return self.host_in_set(host, self.whitelist)
    def record_block(self, first_party):
        self.total_blocked += 1
        if first_party.isValid():
            key = first_party.host().lower()
            if key:
                self.per_host[key] = self.per_host.get(key, 0) + 1
    def blocked_on(self, host):
        return self.per_host.get(host, 0)
class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
    def interceptRequest(self, info):
        engine = self.engine
        if not engine.enabled:
            return
        url = info.requestUrl()
        first_party = info.firstPartyUrl()
        if engine.should_block(url, first_party):
            info.block(True)
            engine.record_block(first_party)
def install_cosmetic_filter(profile):
    script = QWebEngineScript()
    script.setName("honeybell-cosmetic")
    script.setInjectionPoint(QWebEngineScript.DocumentReady)
    script.setRunsOnSubFrames(True)
    script.setWorldId(QWebEngineScript.ApplicationWorld)
    script.setSourceCode(COSMETIC_JS)
    profile.scripts().insert(script)