###
# Copyright (c) 2013, Stacey Ell
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###
from datetime import datetime, timedelta

import supybot.utils as utils
from supybot.commands import wrap
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('PonyCountdown')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

import requests
import execjs
import dateutil
import dateutil.parser
import pytz


pluralization_table = {
    'week': (_('week'), _('weeks')),
    'day': (_('day'), _('days')),
    'hour': (_('hour'), _('hours')),
    'minute': (_('minute'), _('minutes')),
    'second': (_('second'), _('seconds')),
}


def format_unit(val, unit):
    if unit in pluralization_table:
        idx = 0 if val == 1 else 1
        unit = pluralization_table[unit][idx]
    return '{} {}'.format(val, unit)


def format_timedelta(delta, show_weeks=True, atom_joiner=None):
    if atom_joiner is None:
        atom_joiner = utils.str.commaAndify
    days, seconds = delta.days, delta.seconds
    atoms = []
    if show_weeks and days // 7:
        atoms.append(format_unit(days // 7, 'week'))
        days = days % 7
    if days:
        atoms.append(format_unit(days, 'day'))
    if seconds // 3600:
        atoms.append(format_unit(seconds // 3600, 'hour'))
        seconds = seconds % 3600
    if seconds // 60:
        atoms.append(format_unit(seconds // 60, 'minute'))
        seconds = seconds % 60
    if seconds:
        atoms.append(format_unit(seconds, 'second'))
    if not atoms:
        raise ValueError('Time difference not great enough to be noted.')
    return atom_joiner(atoms)


def time_defucker(localtime_str):
    return dateutil.parser.parse(localtime_str) \
        .astimezone(dateutil.tz.tzlocal()) \
        .replace(tzinfo=pytz.utc)


class PonyRecord(object):
    def __init__(self, (when, season, ep_num, ep_name)):
        self.when = time_defucker(when)
        self.season = season
        self.ep_num = ep_num
        self.ep_name = ep_name

    def _inner_repr(self):
        return '({0.when!r}, {0.season!r}, {0.ep_num!r}, {0.ep_name!r})' \
            .format(self)

    def __unicode__(self):
        fmt = u"""S{:03}E{:02} ``{}'' in {}"""
        time_until = format_timedelta(self.when - datetime.now(pytz.utc))
        return fmt.format(self.season, self.ep_num, self.ep_name, time_until)

    def __repr__(self):
        return b'PonyRecord({!s})'.format(self._inner_repr())


class PonyCountdown(callbacks.Plugin):
    """Add the help for "@plugin help PonyCountdown" here
    This should describe *how* to use this plugin."""
    threaded = True
    max_record_age = timedelta(hours=6)

    def __init__(self, *args, **kwargs):
        super(PonyCountdown, self).__init__(*args, **kwargs)
        self._last_checked = datetime(1970, 1, 1)

    def _redownload(self):
        req2 = requests.get('http://ponycountdown.com/api/data.js')
        stuff = execjs.compile(req2.content).eval('ponycountdowndates')
        self._ponyrecords = map(PonyRecord, stuff)
        self._last_checked = datetime.now()

    def _want_redownload(self):
        best_before = (self._last_checked + self.max_record_age)
        return best_before < datetime.now()

    def pony(self, irc, msg, args):
        """

        ponies"""
        if self._want_redownload():
            self._redownload()
        outputs = filter(
            lambda x: datetime.now(pytz.utc) < x.when,
            self._ponyrecords)
        for output in outputs[:3]:
            irc.reply(unicode(output), prefixNick=False)
    pony = wrap(pony)


Class = PonyCountdown


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
