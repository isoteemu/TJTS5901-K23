"""
Hack to get the hosted gitlab magiclink extension to work with mkdocs.

See: https://github.com/facelessuser/pymdown-extensions/issues/933
"""
import pymdownx.magiclink
base_url = "https://gitlab.jyu.fi"
pymdownx.magiclink.PROVIDER_INFO["gitlab"].update({
    "url": base_url,
    "issue": "%s/{}/{}/issues/{}" % base_url,
    "pull": "%s/{}/{}/merge_requests/{}" % base_url,
    "commit": "%s/{}/{}/commit/{}" % base_url,
    "compare": "%s/{}/{}/compare/{}...{}" % base_url,
})

def define_env(env):
    pass
