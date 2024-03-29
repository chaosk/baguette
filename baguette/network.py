import re
from commentary import Player
from constants import *
from utils import ints_to_string
from packer import SANITIZE_CC, SKIP_START_WHITESPACES

class Tick(int):
	pass

class BaseNet(object):
	id = 0
	attr_proto = []
	attributes = {}
	ignorable = False

	def assign_fields(self, values):
		if self.ignorable:
			return # ?!?!?!?
		attr_proto = self.attr_proto
		for i in xrange(len(attr_proto)):
			self.attributes[attr_proto[i][0]] = attr_proto[i][1](values[i])

		self.clean_up()

	def clean_up(self):
		pass

	def concatecate_strings(self, attr_name, num, int_unpack=True):
		alist = [self.attributes['{0}{1}'.format(attr_name, i)] for i in xrange(num)]
		if int_unpack:
			self.attributes[attr_name] = ints_to_string(alist)
		else:
			self.attributes[attr_name] = ''.join(alist)

	def process(self, commentator):
		pass

	def __repr__(self):
		return '<{0} {1}>'.format(self.class_name, self.name)

	def __unicode__(self):
		return self.name


# class Net(BaseNet):
# 	def get_attr_proto(self):
# 		return super(Net, self).attr_proto + [a+[None]*(3-len(a)) for a in self.attr_proto]


class NetObject(BaseNet):
	class_name = 'NetObject'
	item_count = 0

	def process(self, commentator):
		pass


class NetEvent(NetObject):
	class_name = 'NetEvent'


class NetMessage(BaseNet):
	class_name = 'NetMessage'
	unpacker = None

	def process(self, commentator):
		pass

	def get_for_type_str(self, params):
		return self.unpacker.get_string(params)

	def get_for_type_int(self, params):
		return self.unpacker.get_int()

	def get_for_type_bool(self, params):
		return bool(self.get_for_type_int(params))

	def collect_data(self):
		attr_proto = self.attr_proto
		for attribute in attr_proto:
			try:
				attr, atype, params = attribute
			except ValueError:
				attr, atype, params = attribute + [None]
			try:
				self.attributes[attr] = \
					getattr(self, 'get_for_type_{0}'.format(atype.__name__))(params)
			except AttributeError:
				raise TypeError("There is no handler (get_for_type_{0}) for type {0}"
					"used in \"{1}\" attribute.".format(atype.__name__, attr))


class NetMessageCl(NetMessage):
	class_name = 'NetMessageCl'


class NetMessageSv(NetMessage):
	class_name = 'NetMessageSv'


class NetObjectInvalid(NetObject):
	name = 'Invalid'
	ignorable = True


class NetObjectPlayerInput(NetObject):
	id = 1
	name = 'PlayerInput'
	item_count = 10
	ignorable = True

	attr_proto = [
		['direction', int],
		['target_x', int],
		['target_y', int],
		['jump', bool],
		['fire', bool],
		['hook', bool],
		['player_flags', int],
		['wanted_weapon', int],
		['next_weapon', int],
		['prev_weapon', int],
	]


class NetObjectProjectile(NetObject):
	id = 2
	name = 'Projectile'
	item_count = 6
	ignorable = True
	
	attr_proto = [
		['x', int],
		['y', int],
		['vel_x', int],
		['vel_y', int],
		['type', int],
		['start_tick', Tick],
	]


class NetObjectLaser(NetObject):
	id = 3
	name = 'Laser'
	item_count = 5
	ignorable = True

	attr_proto = [
		['x', int],
		['y', int],
		['from_x', int],
		['from_y', int],
		['start_tick', Tick],
	]


class NetObjectPickup(NetObject):
	id = 4
	name = 'Pickup'
	item_count = 4
	ignorable = True

	attr_proto = [
		['x', int],
		['y', int],
		['type', int],
		['subtype', int],
	]


class NetObjectFlag(NetObject):
	id = 5
	name = 'Flag'
	item_count = 3
	ignorable = True

	attr_proto = [
		['x', int],
		['y', int],
		['team', int],
	]


class NetObjectGameInfo(NetObject):
	id = 6
	name = 'GameInfo'
	item_count = 8

	attr_proto = [
		['game_flags', int],
		['gamestate_flags', int],
		['round_start_tick', Tick],
		['warmup_timer', int],
		['score_limit', int],
		['time_limit', int],
		['round_num', int],
		['round_current', int],
	]

	def process(self, commentator):
		commentator.check_for_restart(self.attributes['round_start_tick'])
		commentator.set_score_limit(self.attributes['score_limit'])
		commentator.set_time_limit(self.attributes['time_limit'])

	def clean_up(self):
		self.attributes['is_team_game'] = bool(self.attributes['game_flags'] & 1)
		self.attributes['is_flag_game'] = bool(self.attributes['game_flags'] & 2)
		del self.attributes['game_flags']
		self.attributes['is_gameover'] = bool(self.attributes['gamestate_flags'] & 1)
		self.attributes['is_suddendeath'] = bool(self.attributes['gamestate_flags'] & 2)
		self.attributes['is_paused'] = bool(self.attributes['gamestate_flags'] & 4)
		del self.attributes['gamestate_flags']


class NetObjectGameData(NetObject):
	id = 7
	name = 'GameData'
	item_count = 4

	attr_proto = [
		['red_score', int],
		['blue_score', int],
		['red_flagcarrier_id', int],
		['blue_flagcarrier_id', int],
	]

	def process(self, commentator):
		commentator.set_team_scores(self.attributes['blue_score'],
			self.attributes['red_score'])
		commentator.set_flagcarriers(self.attributes['blue_flagcarrier_id'],
			self.attributes['red_flagcarrier_id'])

class NetObjectCharacterCore(NetObject):
	id = 8
	name = 'CharacterCore'
	item_count = 15
	ignorable = True

	attr_proto = [
		['tick', Tick],
		['x', int],
		['y', int],
		['vel_x', int],
		['vel_y', int],
		['angle', int],
		['direction', int],
		['jumped', int],
		['hooked_player', int],
		['hook_state', int],
		['hook_tick', Tick],
		['hook_x', int],
		['hook_y', int],
		['hook_Dx', int],
		['hook_Dy', int],
	]


class NetObjectCharacter(NetObjectCharacterCore):
	id = 9
	name = 'Character'
	item_count = 22
	ignorable = True

	attr_proto = [
		['tick', Tick],
		['x', int],
		['y', int],
		['vel_x', int],
		['vel_y', int],
		['angle', int],
		['direction', int],
		['jumped', int],
		['hooked_player', int],
		['hook_state', int],
		['hook_tick', Tick],
		['hook_x', int],
		['hook_y', int],
		['hook_Dx', int],
		['hook_Dy', int],
		['player_flags', int],
		['health', int],
		['armor', int],
		['ammo_count', int],
		['weapon', int],
		['emote', int],
		['attack_tick', int],
	]

class NetObjectPlayerInfo(NetObject):
	id = 10
	name = 'PlayerInfo'
	item_count = 5

	attr_proto = [
		['is_local', bool],
		['client_id', int],
		['team', int],
		['score', int],
		['latency', int],
	]

	def process(self, commentator):
		client_id = self.attributes['client_id']
		try:
			commentator.round.players[client_id].score = self.attributes['score']
		except KeyError:
			commentator.round.player_waiting.team = self.attributes['team']
			commentator.set_player(client_id,
				commentator.round.player_waiting)


class NetObjectClientInfo(NetObject):
	id = 11
	name = 'ClientInfo'
	item_count = 17

	attr_proto = [
		['name0', int],
		['name1', int],
		['name2', int],
		['name3', int],

		['clan0', int],
		['clan1', int],
		['clan2', int],
		
		['country', int],
		
		['skin0', int],
		['skin1', int],
		['skin2', int],
		['skin3', int],
		['skin4', int],
		['skin5', int],
		
		['use_custom_color', bool],
		['color_body', int],
		['color_feet', int],
	]

	def process(self, commentator):
		name = self.attributes['name']
		try:
			player = commentator.get_player_by_name(name)
		except KeyError:
			player = Player()
		else:
			return
		player.game = commentator.round
		player.nickname = self.attributes['name']
		player.clanname = self.attributes['clan']
		player.country = self.attributes['country']
		player.join_tick = commentator.demo.current_tick
		commentator.round.player_waiting = player

	def clean_up(self):
		self.concatecate_strings('name', 4)
		self.concatecate_strings('clan', 3)
		self.concatecate_strings('skin', 6)


class NetObjectSpectatorInfo(NetObject):
	id = 12
	name = 'SpectatorInfo'
	item_count = 3
	ignorable = True

	attr_proto = [
		['spectator_id', int],
		['x', int],
		['y', int],
	]


class NetEventCommon(NetEvent):
	id = 13
	name = 'Common'
	item_count = 2
	ignorable = True

	attr_proto = [
		['x', int],
		['y', int],
	]


class NetEventExplosion(NetEventCommon):
	id = 14
	name = 'Explosion'
	ignorable = True


class NetEventSpawn(NetEventCommon):
	id = 15
	name = 'Spawn'
	ignorable = True


class NetEventHammerHit(NetEventCommon):
	id = 16
	name = 'HammerHit'
	ignorable = True


class NetEventDeath(NetEventCommon):
	id = 17
	name = 'Death'
	item_count = 3
	ignorable = True

	attr_proto = [
		['x', int],
		['y', int],
		['client_id', int],
	]


class NetEventSoundGlobal(NetEventCommon):
	id = 18
	# To be removed in 0.7
	name = 'SoundGlobal'
	item_count = 3
	ignorable = True

	attr_proto = [
		['x', int],
		['y', int],
		['sound_id', int],
	]


class NetEventSoundWorld(NetEventCommon):
	id = 19
	name = 'SoundWorld'
	item_count = 3
	ignorable = True

	attr_proto = [
		['x', int],
		['y', int],
		['sound_id', int],
	]


class NetEventDamageInd(NetEventCommon):
	id = 20
	name = 'DamageInd'
	item_count = 3
	ignorable = True

	attr_proto = [
		['x', int],
		['y', int],
		['angle', int],
	]


NET_CLASSES = [
	NetObjectInvalid,
	NetObjectPlayerInput,
	NetObjectProjectile,
	NetObjectLaser,
	NetObjectPickup,
	NetObjectFlag,
	NetObjectGameInfo,
	NetObjectGameData,
	NetObjectCharacterCore,
	NetObjectCharacter,
	NetObjectPlayerInfo,
	NetObjectClientInfo,
	NetObjectSpectatorInfo,
	NetEventCommon,
	NetEventExplosion,
	NetEventSpawn,
	NetEventHammerHit,
	NetEventDeath,
	NetEventSoundGlobal, # To be removed in 0.7
	NetEventSoundWorld,
	NetEventDamageInd,
	NetObjectInvalid
]


def get_net_class_for(atype):
	try:
		if atype < 0:
			raise IndexError
		return NET_CLASSES[atype]
	except IndexError:
		raise IndexError("Unknown Net class ({0})".format(atype))


class NetMessageInvalid(NetMessage):
	name = 'Invalid'
	ignorable = True


class NetMessageSvMotd(NetMessageSv):
	id = 1
	name = 'SvMotd'
	ignorable = True

	attr_proto = [
		['message', str],
	]


class NetMessageSvBroadcast(NetMessageSv):
	id = 2
	name = 'SvBroadcast'

	attr_proto = [
		['message', str],
	]

	def process(self, commentator):
		commentator.event('broadcast', self.attributes['message'])


class NetMessageSvChat(NetMessageSv):
	id = 3
	name = 'SvChat'

	attr_proto = [
		['is_team', bool],
		['client_id', int],
		['message', str],
	]

	def process(self, commentator):
		message = self.attributes['message']
		if self.attributes['client_id'] != CHAT_SERVER:
			return commentator.chat(is_team=self.attributes['is_team'],
				client_id=self.attributes['client_id'],
				message=message)
		else:
			# MISSING:
			#  - name changes
			#  - vote calls
			#  - vote results

			try:
				matches = re.search(r"'(?P<player_name>.*?)' entered and"
					r" joined the (?P<team>[\w\s]+)", message).groupdict()
			except AttributeError:
				pass
			# else:
			# 	commentator.new_player(*matches)

			try:
				matches = re.search(r"'(?P<player_name>.*?)' joined the"
					r" (?P<team>[\w\s]+)", message).groupdict()
			except AttributeError:
				pass
			else:
				return commentator.team_change(**matches)

			try:
				matches = re.search(r"'(?P<player_name>.*?)' has"
					r" left the game( \((?P<reason>.*?)\))?", message).groupdict()
			except AttributeError:
				pass
			else:
				return commentator.player_left(**matches)

			try:
				matches = re.search(r"The (?P<flag_captured>\w+?) flag was"
					r" captured by '(?P<player_name>.*?)'"
					r"( \((?P<time>[\d\.]+) seconds\))?", message).groupdict()
			except AttributeError:
				pass
			else:
				commentator.flag_capture(**matches)

class NetMessageSvKillMsg(NetMessageSv):
	id = 4
	name = 'SvKillMsg'

	attr_proto = [
		['killer', int],
		['victim', int],
		['weapon', int],
		['mode_special', int],
	]

	def process(self, commentator):
		commentator.add_kill(self.attributes['killer'], self.attributes['victim'],
			self.attributes['weapon'], self.attributes['mode_special'])

class NetMessageSvSoundGlobal(NetMessageSv):
	id = 5
	name = 'SvSoundGlobal'
	ignorable = True

	attr_proto = [
		['sound_id', int],
	]


class NetMessageSvTuneParams(NetMessageSv):
	id = 6
	name = 'SvTuneParams'
	ignorable = True


class NetMessageSvExtraProjectile(NetMessageSv):
	id = 7
	name = 'SvExtraProjectile'
	ignorable = True


class NetMessageSvReadyToEnter(NetMessageSv):
	id = 8
	name = 'SvReadyToEnter'
	ignorable = True


class NetMessageSvWeaponPickup(NetMessageSv):
	id = 9
	name = 'SvWeaponPickup'
	ignorable = True

	attr_proto = [
		['weapon', int],
	]


class NetMessageSvEmoticon(NetMessageSv):
	id = 10
	name = 'SvEmoticon'
	ignorable = True

	attr_proto = [
		['client_id', int],
		['emoticon', int],
	]


class NetMessageSvVoteClearOptions(NetMessageSv):
	id = 11
	name = 'SvVoteClearOptions'
	ignorable = True


class NetMessageSvVoteOptionListAdd(NetMessageSv):
	id = 12
	name = 'SvVoteOptionListAdd'
	ignorable = True

	attr_proto = [
		['num_options', int],
		['description0', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['description1', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['description2', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['description3', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['description4', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['description5', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['description6', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['description7', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['description8', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['description9', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['description10', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['description11', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['description12', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['description13', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['description14', str, SANITIZE_CC|SKIP_START_WHITESPACES],
	]

	def clean_up(self):
		self.concatecate_strings('description', 15, int_unpack=False)


class NetMessageSvVoteOptionAdd(NetMessageSv):
	id = 13
	name = 'SvVoteOptionAdd'
	ignorable = True

	attr_proto = [
		['description', str, SANITIZE_CC|SKIP_START_WHITESPACES],
	]


class NetMessageSvVoteOptionRemove(NetMessageSv):
	id = 14
	name = 'SvVoteOptionRemove'
	ignorable = True

	attr_proto = [
		['description', str, SANITIZE_CC|SKIP_START_WHITESPACES],
	]


class NetMessageSvVoteSet(NetMessageSv):
	id = 15
	name = 'SvVoteSet'

	attr_proto = [
		['timeout', int],
		['description', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['reason', str, SANITIZE_CC|SKIP_START_WHITESPACES],
	]


class NetMessageSvVoteStatus(NetMessageSv):
	id = 16
	name = 'SvVoteStatus'
	ignorable = True

	attr_proto = [
		['yes', int],
		['no', int],
		['pass', int],
		['total', int],
	]


class NetMessageClSay(NetMessageCl):
	id = 17
	name = 'ClSay'
	ignorable = True

	attr_proto = [
		['team', bool],
		['message', str],
	]


class NetMessageClSetTeam(NetMessageCl):
	id = 18
	name = 'ClSetTeam'
	ignorable = True

	attr_proto = [
		['team', int],
	]


class NetMessageClSetSpectatorMode(NetMessageCl):
	id = 19
	name = 'ClSetSpectatorMode'
	ignorable = True

	attr_proto = [
		['spectator_id', int],
	]


class NetMessageClStartInfo(NetMessageCl):
	id = 20
	name = 'ClStartInfo'

	attr_proto = [
		['name', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['clan', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['country', int],
		['skin', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['use_custom_color', bool],
		['color_body', int],
		['color_feet', int],
	]


class NetMessageClChangeInfo(NetMessageCl):
	id = 21
	name = 'ClChangeInfo'

	attr_proto = [
		['name', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['clan', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['country', int],
		['skin', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['use_custom_color', bool],
		['color_body', int],
		['color_feet', int],
	]


class NetMessageClKill(NetMessageCl):
	id = 22
	name = 'ClKill'
	ignorable = True


class NetMessageClEmoticon(NetMessageCl):
	id = 23
	name = 'ClEmoticon'
	ignorable = True

	attr_proto = [
		['emoticon', int],
	]


class NetMessageClVote(NetMessageCl):
	id = 24
	name = 'ClVote'
	ignorable = True

	attr_proto = [
		['vote', int],
	]


class NetMessageClCallVote(NetMessageCl):
	id = 25
	name = 'ClCallVote'
	ignorable = True

	attr_proto = [
		['type', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['value', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['reason', str, SANITIZE_CC|SKIP_START_WHITESPACES],
	]


NET_MESSAGES = [
	NetMessageInvalid,
	# Server messages
	NetMessageSvMotd,
	NetMessageSvBroadcast,
	NetMessageSvChat,
	NetMessageSvKillMsg,
	NetMessageSvSoundGlobal,
	NetMessageSvTuneParams,
	NetMessageSvExtraProjectile,
	NetMessageSvReadyToEnter,
	NetMessageSvWeaponPickup,
	NetMessageSvEmoticon,
	NetMessageSvVoteClearOptions,
	NetMessageSvVoteOptionListAdd,
	NetMessageSvVoteOptionAdd,
	NetMessageSvVoteOptionRemove,
	NetMessageSvVoteSet,
	NetMessageSvVoteStatus,

	# Client messages
	NetMessageClSay,
	NetMessageClSetTeam,
	NetMessageClSetSpectatorMode,
	NetMessageClStartInfo,
	NetMessageClChangeInfo,
	NetMessageClKill,
	NetMessageClEmoticon,
	NetMessageClVote,
	NetMessageClCallVote,
	
	NetMessageInvalid,
]


def get_net_message_for(atype):
	try:
		return NET_MESSAGES[atype]
	except IndexError:
		raise IndexError("Unknown NetMessage class")
