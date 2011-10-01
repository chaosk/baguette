from collections import OrderedDict
from constants import *

CONSECUTIVE_CAPS = [0, 'double', 'triple', 'pwnage']
def seconds(num):
	return num * TICKS_PER_SECOND


class Player(object):
	def __init__(self):
		self.nickname = ''
		self.clanname = ''

		self.game = None
		self.join_tick = 0
		self.leave_tick = 0
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
		return ((self.leave_tick if self.leave_tick else
			self.game.end_tick if self.game.end_tick else
			self.demo.current_tick) - self.join_tick - self.time_away) // TICKS_PER_SECOND

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
		self.last_capture_tick = 0
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


class GameRound(object):

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
		self.end_tick = 0
		self.start_game_tick = 0
		self.no_touches = True

		self.demo = None

		self.spectators = Spectators()
		self.blue = Blue()
		self.red = Red()
		self.teams = {
			TEAM_SPECTATOR: self.spectators,
			TEAM_BLUE: self.blue,
			TEAM_RED: self.red,
		}
		self.commentary = Commentary()

	def get_player(self, name):
		return self.players[self.players_name_to_id[name]]

	@property
	def duration(self):
		return ((self.end_tick if self.end_tick else
			self.demo.current_tick) - self.start_tick) // TICKS_PER_SECOND


class Commentary(object):
	
	def __init__(self):
		self.commentary = {}

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


class Commentator(object):

	def __init__(self, demo):
		self.demo = demo

	def first_new_round(self):
		around = GameRound()
		around.demo = self.demo
		self.new_round = self.next_new_round
		self.demo.rounds.append(around)

	def next_new_round(self):
		current_tick = self.demo.current_tick
		self.round.end_tick = current_tick
		around = GameRound()
		around.demo = self.demo
		around.start_tick = current_tick
		self.demo.rounds.append(around)
		
	@property
	def round(self):
		return self.demo.rounds[-1]

	new_round = first_new_round

	def comment(self, atype, message, params=None):
		adict = {'type': atype, 'message': message, 'params': params}
		timestamp = (self.demo.current_tick - self.round.start_tick) // SNAPS_PER_SECOND
		
		try:
			self.round.commentary.commentary[timestamp].append(adict)
		except KeyError:
			self.round.commentary.commentary[timestamp] = [adict]

	def event(self, atype, message, params=None):
		self.comment(atype, message, params)

	def game_conditions(self, message):
		self.event('game_conditions', message)

	def chat(self, is_team, client_id, message):
		try:
			player = self.round.players[client_id]
		except KeyError:
			return

		self.event('chat', "[{0}] {1}: {2}".format(
			"global" if not is_team else "team/{0}".format(
			TEAMS[player.team].lower()), player.nickname, message)
		)

	def set_score_limit(self, score_limit):
		if score_limit == self.round.score_limit:
			return
		if score_limit:
			self.game_conditions("Score limit changed to {0}".format(score_limit))
		else:
			self.game_conditions("Score limit disabled")
		self.round.score_limit = score_limit

	def set_time_limit(self, time_limit):
		if time_limit == self.round.time_limit:
			return
		if time_limit:
			self.game_conditions("Time limit changed to {0}".format(time_limit))
		else:
			self.game_conditions("Time limit disabled")
		self.round.time_limit = time_limit

	def restart(self, start_tick):
		self.new_round()
		self.event('restart', "Game restarted.")
		self.round.start_game_tick = start_tick

	def first_check_for_restart(self, start_tick):
		self.restart(start_tick)
		self.check_for_restart = self.next_check_for_restart

	def next_check_for_restart(self, start_tick):
		if self.round.start_game_tick != start_tick:
			self.restart(start_tick)
			self.round.start_game_tick = start_tick

	check_for_restart = first_check_for_restart

	def set_team_scores(self, blue_score, red_score):
		if self.round.blue.score != blue_score:
			self.round.blue.score = blue_score
		if self.round.red.score != red_score:
			self.round.red.score = red_score

	def update_flag_possession(self, team):
		round = self.round
		flag_history = team.current_flag_history
		try:
			current_flag_item = flag_history[-1]
		except IndexError:
			return
		else:
			current_flag_carrier_id = current_flag_item['flag_carrier_id']
			flag_time = self.demo.current_tick - current_flag_item['tick']
		try:
			current_flag_item['flag_carrier'].flag_possession += flag_time
		except AttributeError:
			pass
		team.flag_possession += flag_time

	def flag_history_item(self, team, flag_carrier_id):
		try:
			flag_carrier = self.round.players[flag_carrier_id]
		except KeyError:
			return
		flag_history = team.current_flag_history
		self.update_flag_possession(team)
		adict = {'flag_carrier_id': flag_carrier_id,
			'flag_carrier': flag_carrier, 'tick': self.demo.current_tick}
		flag_history.append(adict)

	def flag_history_clear(self, team):
		self.update_flag_possession(team)
		team.current_flag_history = []

	def set_flagcarrier(self, team_id, flagcarrier_id):
		team = self.round.teams[OPPONENTS[team_id]]
		if team.flag_carrier != flagcarrier_id:
			if flagcarrier_id >= 0:
				self.flag_history_item(team, flagcarrier_id)
				if team.flag_carrier == FLAG_ATSTAND:
					try:
						player = self.round.players[flagcarrier_id]
					except KeyError:
						return
					if self.round.no_touches:
						self.round.no_touches = False
						self.event('first_touch', "First flag touch by {0} ({1})".format(player.nickname, team.short))
					if self.demo.current_tick - team.last_capture_tick < seconds(5):
						team.possible_consecutive_cap = True
					if self.demo.current_tick - self.round.teams[OPPONENTS[team_id]].last_capture_tick < seconds(5):
						team.possible_counter_cap = True
					team.flag_touches += 1
					if not team.flag_touches % 100: 
						self.event('capture_by_touches', "100 flag touches by {0}".format(team.lower()))
					player.flag_touches += 1
			elif flagcarrier_id == FLAG_TAKEN:
				self.flag_history_item(team, flagcarrier_id)
			elif flagcarrier_id == FLAG_ATSTAND:
				self.flag_history_clear(team)
				team.current_assist = None
				team.possible_consecutive_cap = False
				team.consecutive_caps = 0
			team.flag_carrier = flagcarrier_id

	def set_flagcarriers(self, blue_flagcarrier_id, red_flagcarrier_id):
		self.set_flagcarrier(TEAM_BLUE, blue_flagcarrier_id)
		self.set_flagcarrier(TEAM_RED, red_flagcarrier_id)

	def set_player(self, id, player):
		self.round.players[id] = player
		self.round.players_name_to_id[player.nickname] = id

	def get_player_by_name(self, player_name):
		return self.round.players[self.round.players_name_to_id[player_name]]

	def move_player_to_active(self, player_name):
		try:
			player = self.round.players_left[player_name]
		except KeyError:
			return
		player.time_away = self.demo.current_tick - player.leave_tick
		player.leave_tick = 0
		del self.round.players_left[player_name]

	def move_player_to_left(self, player_id):
		player = self.round.players[player_id]
		player.leave_tick = self.demo.current_tick
		self.round.players_left[player.nickname] = player
		del self.round.players[player_id]
		del self.round.players_name_to_id[player.nickname]

	def player_left(self, player_name, reason=None):
		try:
			player_id = self.round.players_name_to_id[player_name]
		except KeyError:
			return
		self.move_player_to_left(player_id)

	def team_change(self, player_name, team):
		team_id = TEAM_NAMES[team]
		try:
			player_id = self.round.players_name_to_id[player_name]
		except KeyError:
			return
		player = self.round.players[player_id]
		if player.team >= 0 and team_id < 0:
			self.move_player_to_left(player_id)
		elif player.team < 0 and team_id >= 0:
			self.move_player_to_active(player_name)
		player.team = team_id

	def flag_capture(self, flag_captured, player_name, time=None):
		try:
			self.get_player_by_name(player_name).flag_captures += 1
		except KeyError:
			return

		team_id = FLAG_CAPTURES_TO_TEAMS[flag_captured]
		team = self.round.teams[team_id]
		team.flag_captures += 1
		team.last_capture_tick = self.demo.current_tick

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

		killer = self.round.players[killer_id]

		if killer_id == victim_id and victim_id > -1:
			victim = killer
			victim.suicides += 1
		else:
			victim = self.round.players[victim_id]
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
			self.round.teams[killer.team].current_assist = killer
			killer.carriers_killed += 1
		if mode_special & 2:
			if killer_id != victim_id:
				killer.kills_holding_flag += 1
			victim.deaths_holding_flag += 1
