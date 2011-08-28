from constants import *

class Player(object):
	nickname = ''
	clanname = ''

	game = None
	join_timestamp = 0
	leave_timestamp = 0
	
	team = -1
	score = 0
	kills = 0
	deaths = 0
	suicides = 0
	current_spree = 0
	best_spree = 0
	hammer_kills = 0
	hammer_deaths = 0
	pistol_kills = 0
	pistol_deaths = 0
	shotgun_kills = 0
	shotgun_deaths = 0
	grenade_kills = 0
	grenade_deaths = 0
	rifle_kills = 0
	rifle_deaths = 0
	flag_touches = 0
	flag_captures = 0
	carriers_killed = 0
	kills_holding_flag = 0
	deaths_holding_flag = 0

	@property
	def kills_per_minute(self):
		try:
			return self.kills / (self.time_played / 60)
		except ZeroDivisionError:
			return 0

	@property
	def net_score(self):
		return self.kills - self.deaths

	@property
	def ratio(self):
		try:
			return self.kills / self.deaths
		except ZeroDivisionError:
			return float('inf')

	@property
	def time_played(self):
		return leave_timestamp - join_timestamp


class Game(object):
	duration = 0 # in ticks
	score_limit = 0
	time_limit = 0
	player_count = 0

	blue_score = 0
	red_score = 0

	blue_flagcarrier = None
	red_flagcarrier = None

	player_waiting = None
	start_tick = 0


class Commentary(object):
	# {id: Player...}
	players = {}
	players_left = {}

	game = Game()

	# text repr,
	# {timestamp: [str, str, str]}
	commentary = {}

	current_tick = 0

	@property
	def current_timestamp(self):
		return self.current_tick // 50

	def get_player(self, id):
		try:
			player = self.players[id]
		except KeyError:
			player = None
		return player

	def comment(self, atype, subtype, message):
		try:
			self.commentary[self.current_timestamp].append({'type': atype,
				'subtype': subtype, 'message': message})
		except KeyError:
			self.commentary[self.current_timestamp] = [{'type': atype,
				'subtype': subtype, 'message': message}]

	def event(self, subtype, message):
		self.comment('event', subtype, message)

	def game_conditions(self, message):
		self.event('game_conditions', message)

	def chat(self, team, client_id, message):
		player = self.get_player(client_id)
		self.event('chat', "[{0}] {1}: {2}".format(
			"global" if team == CHAT_ALL else "team/{0}".format(
			TEAMS[team].lower()), player, message)
		)

	def set_timestamp(self, timestamp):
		self.current_timestamp = timestamp

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

	def restart(self, start_tick):
		self.game = Game()
		self.players = {}
		self.players_left = {}
		self.commentary = {}
		self.game.start_tick = start_tick

	def check_for_restart(self, start_tick):
		if not self.game.start_tick:
			self.game.start_tick = start_tick
		elif self.game.start_tick != start_tick:
			self.restart(start_tick)

	def set_team_scores(self, blue_score, red_score):
		self.game.blue_score = blue_score
		self.game.red_score = red_score

	def set_flagcarriers(self, blue_flagcarrier, red_flagcarrier):
		self.game.blue_flagcarrier = blue_flagcarrier
		self.game.red_flagcarrier = red_flagcarrier

	def set_player(self, id, player):
		self.players[id] = player
