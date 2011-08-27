
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


class Commentary(object):
	# {id: Player...}
	players = {}
	players_left = {}

	# text repr,
	# {timestamp: [str, str, str]}
	commentary = {}

	current_tick = 0
	current_timestamp = 0

	def new_tick(self, tick):
		self.game[tick] = {'objects': {}, 'messages': {}}

	def set_timestamp(self, timestamp):
		self.current_timestamp = timestamp
