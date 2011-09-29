from collections import OrderedDict
from copy import copy

from constants import *

CONSECUTIVE_CAPS = [0, 'double', 'triple', 'pwnage']
def seconds(num):
	return num * TICKS_PER_SECOND

class Player(object):
	def __init__(self):
		self.nickname = ''
		self.clanname = ''

		self.game = None
		self.join_timestamp = 0
		self.leave_timestamp = 0
		self.time_away = 0
	
		self.team = TEAM_SPECTATOR
		self.score = 0
		self.kills = 0
		self.deaths = 0
		self.suicides = 0
		self.current_spree = 0
		self.best_spree = 0
		self.weapon_kills = [0, 0, 0, 0, 0, 0]
		self.weapon_deaths = [0, 0, 0, 0, 0, 0]
		self.assists = 0
		self.flag_possession = 0
		self.flag_touches = 0
		self.flag_captures = 0
		self.carriers_killed = 0
		self.kills_holding_flag = 0
		self.deaths_holding_flag = 0

	@property
	def kills_per_minute(self):
		try:
			return self.kills / (self.time_played / 60.0)
		except ZeroDivisionError:
			return 0

	@property
	def net_score(self):
		return self.kills - self.deaths

	@property
	def ratio(self):
		try:
			return float(self.kills) / self.deaths
		except ZeroDivisionError:
			return float('inf')

	@property
	def time_played(self):
		return (self.leave_timestamp if self.leave_timestamp else
			self.game.current_timestamp) - self.join_timestamp - self.time_away

	def detailed_scoreboard(self):
		headings = ("Nickname", "Clan", "Score", "Kills", "Deaths",
			"Suicides", "K/D", "K/Min.", "Flag grabs", "Flag captures")
		fields = ("nickname", "clanname", "score", "kills", "deaths",
			"suicides", "ratio", "kills_per_minute", "flag_touches", "flag_captures")
		rules = ("s", "s", "n", "n", "n", "n", ".2f", ".2f", "n", "n")
		return '\n'.join(["{0}\n\t{1:{2}}".format(headings[i],
			getattr(self, fields[i]), rules[i])
			for i in xrange(len(headings))] + \
			["Time played\n\t{0:02n}:{1:02n}" \
			.format(*divmod(self.time_played, 60))] + \
			["{0}\n\t{1} / {2}".format(WEAPONS[i],
			self.weapon_kills[i], self.weapon_deaths[i])
			for i in xrange(len(self.weapon_kills))])

	def __unicode__(self):
		return self.nickname

	def __repr__(self):
		return "<Player {0}>".format(self.nickname)


class Team(object):
	name = "Unknown"

	def __init__(self):
		self.score = 0
		self.flag_carrier = FLAG_ATSTAND
		self.flag_touches = 0
		self.flag_captures = 0
		self.flag_possession = 0
		self.last_capture_time = 0
		self.possible_consecutive_cap = False
		self.possible_counter_cap = False
		self.consecutive_caps = 0
		self.current_assist = None
		self.current_flag_history = []

	def __repr__(self):
		return self.name


class Blue(Team):
	name = "Blue team"
	short = "blue"


class Red(Team):
	name = "Red team"
	short = "red"


class Spectators(Team):
	name = "Spectators"
	short = "spect"


class Game(object):
	def __init__(self):
		self.score_limit = 0
		self.time_limit = 0
		self.player_count = 0
		self.blue_score = 0
		self.red_score = 0
		self.players = {}
		self.players_name_to_id = {}
		self.players_left = {}
		self.player_waiting = None
		self.start_tick = 0
		self.current_tick = 0
		self.no_touches = True

		self.spectators = Spectators()
		self.blue = Blue()
		self.red = Red()

		self.teams = {
			TEAM_SPECTATOR: self.spectators,
			TEAM_BLUE: self.blue,
			TEAM_RED: self.red,
		}

	@property
	def current_timestamp(self):
		return self.current_tick // TICKS_PER_SECOND

class Commentary(object):

	game = Game()
	# rounds?
	previous_games = []

	previous_commentaries = []
	commentary = {}

	def get_output(self):
		commentary = OrderedDict(sorted(self.commentary.items(), key=lambda t: t[0]))
		return '\n'.join([
			'[{0:02d}:{1:02d}] [{2}]{3} {4}'.format(
				tick // 60, tick % 60,
				comment['type'],
				' [{0}]'.format(' '.join(comment['params'])) if comment['params'] else '',
				comment['message']
			)
			for tick, comments in commentary.iteritems()
			for comment in comments
		])

	def get_player(self, id):
		try:
			player = self.game.players[id]
		except KeyError:
			player = None
		return player

	def comment(self, atype, message, params=None):
		adict = {'type': atype, 'message': message, 'params': params}
		try:
			self.commentary[self.game.current_timestamp].append(adict)
		except KeyError:
			self.commentary[self.game.current_timestamp] = [adict]

	def event(self, atype, message, params=None):
		self.comment(atype, message, params)

	def game_conditions(self, message):
		self.event('game_conditions', message)

	def chat(self, is_team, client_id, message):
		player = self.get_player(client_id)
		if player == None:
			return
			
		self.event('chat', "[{0}] {1}: {2}".format(
			"global" if not is_team else "team/{0}".format(
			TEAMS[player.team].lower()), player.nickname, message)
		)

	def set_timestamp(self, timestamp):
		self.game.current_timestamp = timestamp

	def set_score_limit(self, score_limit):
		if score_limit == self.game.score_limit:
			return
		if score_limit:
			self.game_conditions("Score limit changed to {0}".format(score_limit))
		else:
			self.game_conditions("Score limit disabled")
		self.game.score_limit = score_limit

	def set_time_limit(self, time_limit):
		if time_limit == self.game.time_limit:
			return
		if time_limit:
			self.game_conditions("Time limit changed to {0}".format(time_limit))
		else:
			self.game_conditions("Time limit disabled")
		self.game.time_limit = time_limit

	def next_tick(self):
		self.game.current_tick += 1

	def restart(self, start_tick):
		self.previous_games.append(self.game)
		self.game = Game()
		self.previous_commentaries.append(copy(self))
		self.commentary = {}
		self.event('restart', "Game restarted.")
		self.game.start_tick = start_tick

	def check_for_restart(self, start_tick):
		if not self.game.start_tick:
			self.game.start_tick = start_tick
		elif self.game.start_tick != start_tick:
			self.restart(start_tick)

	def set_team_scores(self, blue_score, red_score):
		if self.game.blue.score != blue_score:
			self.game.blue.score = blue_score
		if self.game.red.score != red_score:
			self.game.red.score = red_score

	def update_flag_possession(self, team):
		game = self.game
		flag_history = team.current_flag_history
		try:
			current_flag_item = flag_history[-1]
		except IndexError:
			return
		else:
			current_flag_carrier_id = current_flag_item['flag_carrier_id']
			flag_time = game.current_timestamp - current_flag_item['timestamp']
		if current_flag_carrier_id >= 0:
			try:
				current_flag_item['flag_carrier'].flag_possession += flag_time
			except AttributeError:
				pass
			team.flag_possession += flag_time

	def flag_history_item(self, team, flag_carrier_id):
		game = self.game
		flag_history = team.current_flag_history
		self.update_flag_possession(team)
		flag_carrier = self.get_player(flag_carrier_id)
		adict = {'flag_carrier_id': flag_carrier_id,
			'flag_carrier': flag_carrier, 'timestamp': game.current_timestamp}
		flag_history.append(adict)

	def flag_history_clear(self, team):
		self.update_flag_possession(team)
		team.current_flag_history = []

	def set_flagcarrier(self, team_id, flagcarrier):
		team = self.game.teams[OPPONENTS[team_id]]
		if team.flag_carrier != flagcarrier:
			if flagcarrier >= 0:
				self.flag_history_item(team, flagcarrier)
				if team.flag_carrier == FLAG_ATSTAND:
					player = self.get_player(flagcarrier)
					if player == None:
						return
					if self.game.no_touches:
						self.game.no_touches = False
						self.event('first_touch', "First flag touch by {0} ({1})".format(player.nickname, team.short))
					if self.game.current_tick - team.last_capture_time < seconds(5):
						team.possible_consecutive_cap = True
					if self.game.current_tick - self.game.teams[OPPONENTS[team_id]].last_capture_time < seconds(5):
						team.possible_counter_cap = True
					team.flag_touches += 1
					if not team.flag_touches % 100:
						self.event('capture_by_touches', "100 flag touches by {0}".format(team.lower()))
					player.flag_touches += 1
						
			elif flagcarrier == FLAG_TAKEN:
				self.flag_history_item(team, flagcarrier)
			elif flagcarrier == FLAG_ATSTAND:
				self.flag_history_clear(team)
				team.current_assist = None
				team.possible_consecutive_cap = False
				team.consecutive_caps = 0
			team.flag_carrier = flagcarrier


	def set_flagcarriers(self, blue_flagcarrier, red_flagcarrier):
		self.set_flagcarrier(TEAM_BLUE, blue_flagcarrier)
		self.set_flagcarrier(TEAM_RED, red_flagcarrier)

	def set_player(self, id, player):
		self.game.players[id] = player
		self.game.players_name_to_id[player.nickname] = id

	def get_player_by_name(self, player_name):
		try:
			return self.get_player(self.game.players_name_to_id[player_name])
		except KeyError:
			return None

	def move_player_to_active(self, player_name):
		try:
			player = self.game.players_left[player_name]
		except KeyError:
			return
		player.time_away = self.game.current_timestamp - player.leave_timestamp
		player.leave_timestamp = 0
		del self.game.players_left[player_name]

	def move_player_to_left(self, player_id):
		player = self.get_player(player_id)
		player.leave_timestamp = self.game.current_timestamp
		self.game.players_left[player.nickname] = player
		del self.game.players[player_id]
		del self.game.players_name_to_id[player.nickname]

	def player_left(self, player_name, reason=None):
		try:
			player_id = self.game.players_name_to_id[player_name]
		except KeyError:
			return
		self.move_player_to_left(player_id)

	def team_change(self, player_name, team):
		team_id = TEAM_NAMES[team]
		try:
			player_id = self.game.players_name_to_id[player_name]
		except KeyError:
			return
		player = self.get_player(player_id)
		if player.team >= 0 and team_id < 0:
			self.move_player_to_left(player_id)
		elif player.team < 0 and team_id >= 0:
			self.move_player_to_active(player_name)
		player.team = team_id

	def flag_capture(self, flag_captured, player_name, time=None):
		try:
			self.get_player_by_name(player_name).flag_captures += 1
		except:
			import pdb
			pdb.set_trace()
			
		team_id = FLAG_CAPTURES_TO_TEAMS[flag_captured]
		team = self.game.teams[team_id]
		team.flag_captures += 1
		team.last_capture_time = self.game.current_tick

		try:
			team.current_assist.assists += 1
		except AttributeError:
			# ok, no assist
			pass

		extra_params = []
		if team.possible_consecutive_cap:
			try:
				cap_name = CONSECUTIVE_CAPS[team.consecutive_caps]
			except IndexError:
				cap_name = 'pwnage'
			extra_params.append(cap_name)
			team.consecutive_caps += 1
		else:
			extra_params.append('single')

		if team.possible_counter_cap:
			extra_params.append('counter')

		self.event('capture', "The {0} flag was captured by {1}{2}!".format(
			flag_captured,
			player_name,
			' in {0} seconds'.format(time) if time else ''),
			params=(extra_params),
		)

		current_flag_history = [item['flag_carrier'].nickname \
			for item in team.current_flag_history if item['flag_carrier']]
		if len(current_flag_history) > 1:
			self.event('passes', "Passes: {0}".format(', '.join(current_flag_history)))

	def add_kill(self, killer_id, victim_id, weapon_id, mode_special):
		if weapon_id == WEAPON_GAME:
			return

		killer = self.get_player(killer_id)

		if killer_id == victim_id and victim_id > -1:
			victim = killer
			victim.suicides += 1
		else:
			victim = self.get_player(victim_id)
			killer.kills += 1
			killer.current_spree += 1

		victim.deaths += 1
		victim.current_spree = 0
		if victim.current_spree > victim.best_spree:
			victim.best_spree = victim.current_spree

		if weapon_id > -1:
			if killer_id != victim_id:
				killer.weapon_kills[weapon_id] += 1
			victim.weapon_deaths[weapon_id] += 1

		if mode_special & 1 and killer_id != victim_id:
			self.game.teams[killer.team].current_assist = killer
			killer.carriers_killed += 1
		if mode_special & 2:
			if killer_id != victim_id:
				killer.kills_holding_flag += 1
			victim.deaths_holding_flag += 1
