"""
Test helpers for Comprehensive Theming.
"""

from functools import wraps
import os
import os.path
import contextlib

from mock import patch

from django.conf import settings
from django.template import Engine
from django.contrib.sites.models import Site

import edxmako
from .models import SiteTheme


def with_comprehensive_theme(theme_dir_name):
    """
    A decorator to run a test with a comprehensive theming enabled.
    Arguments:
        theme_dir_name (str): directory name of the site for which we want comprehensive theming enabled.
    """
    # This decorator creates Site and SiteTheme models for given domain
    def _decorator(func):                       # pylint: disable=missing-docstring
        @wraps(func)
        def _decorated(*args, **kwargs):        # pylint: disable=missing-docstring
            # themes_dir = settings.COMPREHENSIVE_THEME_DIR
            # if not themes_dir:
            #     themes_dir = "/".join([settings.REPO_ROOT, "themes"])
            #
            domain = "example.com"
            site, __ = Site.objects.get_or_create(domain=domain, name=domain)
            SiteTheme.objects.get_or_create(site=site, theme_dir_name=theme_dir_name)

            # default_engine = Engine.get_default()
            # dirs = default_engine.dirs[:]
            # with edxmako.save_lookups():
            #     edxmako.paths.add_lookup('main', themes_dir, prepend=True)
            #     dirs.insert(0, themes_dir)
            #     with patch.object(default_engine, 'dirs', dirs):
            with patch('openedx.core.djangoapps.theming.helpers.get_current_site', return_value=site):
                    return func(*args, **kwargs)
        return _decorated
    return _decorator


def with_is_edx_domain(is_edx_domain):
    """
    A decorator to run a test as if request originated from edX domain or not.

    Arguments:
        is_edx_domain (bool): are we an edX domain or not?

    """
    # This is weird, it's a decorator that conditionally applies other
    # decorators, which is confusing.
    def _decorator(func):                       # pylint: disable=missing-docstring
        if is_edx_domain:
            # This applies @with_comprehensive_theme to the func.
            func = with_comprehensive_theme('edx.org')(func)

        return func

    return _decorator


@contextlib.contextmanager
def with_edx_domain_context(is_edx_domain):
    """
    A function to run a test as if request originated from edX domain or not.

    Arguments:
        is_edx_domain (bool): are we an edX domain or not?

    """
    if is_edx_domain:
        domain = 'edx.org'
        site, __ = Site.objects.get_or_create(domain=domain, name=domain)
        SiteTheme.objects.get_or_create(site=site, theme_dir_name=domain)

        with patch('openedx.core.djangoapps.theming.helpers.get_current_site', return_value=site):
            yield
    else:
        yield


def dump_theming_info():
    """Dump a bunch of theming information, for debugging."""
    for namespace, lookup in edxmako.LOOKUP.items():
        print "--- %s: %s" % (namespace, lookup.template_args['module_directory'])
        for directory in lookup.directories:
            print "  %s" % (directory,)

    print "=" * 80
    for dirname, __, filenames in os.walk(settings.MAKO_MODULE_DIR):
        print "%s ----------------" % (dir,)
        for filename in sorted(filenames):
            if filename.endswith(".pyc"):
                continue
            with open(os.path.join(dirname, filename)) as f:
                content = len(f.read())
            print "    %s: %d" % (filename, content)
