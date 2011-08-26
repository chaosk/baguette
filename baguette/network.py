from utils import ints_to_string
from packer import SANITIZE_CC, SKIP_START_WHITESPACES

class Tick(int):
	pass


class DictOnSteroids(dict):
	def __getattr__(self, name):
		try:
			return self.__getitem__(name)
		except KeyError:
			raise AttributeError(name)


class BaseNet(object):
	id = 0
	attr_proto = []
	ignorable = False

	def __init__(self):
		self.attributes = DictOnSteroids()

	def get_attr_proto(self):
		return []

	def assign_fields(self, values):
		if self.ignorable:
			return # ?!?!?!?
		attr_proto = self.get_attr_proto()
		for i in xrange(len(attr_proto)):
			if not isinstance(values[i], attr_proto[i][1]):
				# try to simply cast it
				values[i] = attr_proto[i][1](values[i])
			if not isinstance(values[i], attr_proto[i][1]) and not isinstance(values[i], long):
				
				raise TypeError
			self.attributes[attr_proto[i][0]] = values[i]

		self.clean_up()

	def clean_up(self):
		pass

	def concatecate_strings(self, attr_name, num, int_unpack=True):
		alist = []
		for i in xrange(num):
			attr = self.attributes['{0}{1}'.format(attr_name, i)]
			alist.append(attr)
			del attr
		if int_unpack:
			self.attributes[attr_name] = ints_to_string(alist)
		else:
			self.attributes[attr_name] = ''.join(alist)

	def __repr__(self):
		return '<{0} {1}#{2}>'.format(self.class_name, self.name, self.id)

	def __unicode__(self):
		return self.name


class Net(BaseNet):
	def get_attr_proto(self):
		return super(Net, self).get_attr_proto() + [a+[None]*(3-len(a)) for a in self.attr_proto]


class NetObject(Net):
	class_name = 'NetObject'


class NetEvent(Net):
	class_name = 'NetEvent'


class NetMessage(Net):
	class_name = 'NetMessage'
	unpacker = None

	def get_for_type_str(self, params):
		return self.unpacker.get_string(params)

	def get_for_type_int(self, params):
		return self.unpacker.get_int()

	def get_for_type_bool(self, params):
		return bool(self.get_for_type_int(params))

	def collect_data(self):
		attr_proto = self.get_attr_proto()
		for attr, atype, params in attr_proto:
			try:
				self.attributes[attr] = \
					getattr(self, 'get_for_type_{0}'.format(atype.__name__))(params)
			except AttributeError:
				raise TypeError("Wrong type used for "
					" attribute \"{0}\" ({1})".format(attr, atype.__name__))


class NetMessageCl(NetMessage):
	class_name = 'NetMessageCl'


class NetMessageSv(NetMessage):
	class_name = 'NetMessageSv'


class NetObjectInvalid(NetObject):
	name = 'Invalid'
	ignorable = True


class NetObjectPlayerInput(NetObject):
	name = 'PlayerInput'
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
	name = 'Projectile'
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
	name = 'Laser'
	ignorable = True

	attr_proto = [
		['x', int],
		['y', int],
		['from_x', int],
		['from_y', int],
		['start_tick', Tick],
	]


class NetObjectPickup(NetObject):
	name = 'Pickup'
	ignorable = True

	attr_proto = [
		['x', int],
		['y', int],
		['type', int],
		['subtype', int],
	]


class NetObjectFlag(NetObject):
	name = 'Flag'
	ignorable = True

	attr_proto = [
		['x', int],
		['y', int],
		['team', int],
	]


class NetObjectGameInfo(NetObject):
	name = 'GameInfo'

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

	def clean_up(self):
		self.attributes.is_team_game = bool(self.attributes.game_flags & 1)
		self.attributes.is_flag_game = bool(self.attributes.game_flags & 2)
		del self.attributes['game_flags']
		self.attributes.is_gameover = bool(self.attributes.gamestate_flags & 1)
		self.attributes.is_suddendeath = bool(self.attributes.gamestate_flags & 2)
		self.attributes.is_paused = bool(self.attributes.gamestate_flags & 4)
		del self.attributes['gamestate_flags']


class NetObjectGameData(NetObject):
	name = 'GameData'

	attr_proto = [
		['blue_score', int],
		['red_score', int],
		['red_flagcarrier_id', int],
		['blue_flagcarrier_id', int],
	]


class NetObjectCharacterCore(NetObject):
	name = 'CharacterCore'
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
	name = 'Character'

	attr_proto = [
		['player_flags', int],
		['health', int],
		['armor', int],
		['ammo_count', int],
		['weapon', int],
		['emote', int],
		['attack_tick', int],
	]


class NetObjectPlayerInfo(NetObject):
	name = 'PlayerInfo'

	attr_proto = [
		['is_local', bool],
		['client_id', int],
		['team', int],
		['score', int],
		['latency', int],
	]


class NetObjectClientInfo(NetObject):
	name = 'ClientInfo'

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

	def clean_up(self):
		self.concatecate_strings('name', 4)
		self.concatecate_strings('clan', 3)
		self.concatecate_strings('skin', 6)


class NetObjectSpectactorInfo(NetObject):
	name = 'SpectactorInfo'

	attr_proto = [
		['spectactor_id', int],
		['x', int],
		['y', int],
	]


class NetEventCommon(NetEvent):
	name = 'Common'
	ignorable = True

	attr_proto = [
		['x', int],
		['y', int],
	]


class NetEventExplosion(NetEventCommon):
	name = 'Explosion'


class NetEventSpawn(NetEventCommon):
	name = 'Spawn'


class NetEventHammerHit(NetEventCommon):
	name = 'HammerHit'


class NetEventDeath(NetEventCommon):
	name = 'Death'

	attr_proto = [
		['client_id', int],
	]


class NetEventSoundGlobal(NetEventCommon):
	# To be removed in 0.7
	name = 'SoundGlobal'

	attr_proto = [
		['sound_id', int],
	]


class NetEventSoundWorld(NetEventCommon):
	name = 'SoundWorld'

	attr_proto = [
		['sound_id', int],
	]


class NetEventDamageInd(NetEventCommon):
	name = 'DamageInd'

	attr_proto = [
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
	NetObjectSpectactorInfo,
	NetEventCommon,
	NetEventExplosion,
	NetEventSpawn,
	NetEventHammerHit,
	NetEventDeath,
	NetEventSoundGlobal, # To be removed in 0.7
	NetEventSoundWorld,
	NetEventDamageInd,
]


def get_net_class_for(atype):
	try:
		return NET_CLASSES[atype]
	except IndexError:
		raise IndexError("Unknown Net class")


class NetMessageSvMotd(NetMessageSv):
	name = 'SvMotd'

	attr_proto = [
		['message', str],
	]


class NetMessageSvBroadcast(NetMessageSv):
	name = 'SvBroadcast'

	attr_proto = [
		['message', str],
	]


class NetMessageSvChat(NetMessageSv):
	name = 'SvChat'

	attr_proto = [
		['team', int],
		['client_id', int],
		['message', str],
	]


class NetMessageSvKillMsg(NetMessageSv):
	name = 'SvKillMsg'

	attr_proto = [
		['killer', int],
		['victim', int],
		['weapon', int],
		['mode_special', int],
	]


class NetMessageSvSoundGlobal(NetMessageSv):
	name = 'SvSoundGlobal'

	attr_proto = [
		['sound_id', int],
	]


class NetMessageSvTuneParams(NetMessageSv):
	name = 'SvTuneParams'


class NetMessageSvExtraProjectile(NetMessageSv):
	name = 'SvExtraProjectile'


class NetMessageSvReadyToEnter(NetMessageSv):
	name = 'SvReadyToEnter'


class NetMessageSvWeaponPickup(NetMessageSv):
	name = 'SvWeaponPickup'

	attr_proto = [
		['weapon', int],
	]


class NetMessageSvEmoticon(NetMessageSv):
	name = 'SvEmoticon'

	attr_proto = [
		['client_id', int],
		['emoticon', int],
	]


class NetMessageSvVoteClearOptions(NetMessageSv):
	name = 'SvVoteClearOptions'


class NetMessageSvVoteOptionListAdd(NetMessageSv):
	name = 'SvVoteOptionListAdd'

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
	name = 'SvVoteOptionAdd'

	attr_proto = [
		['description', str, SANITIZE_CC|SKIP_START_WHITESPACES],
	]


class NetMessageSvVoteOptionRemove(NetMessageSv):
	name = 'SvVoteOptionRemove'

	attr_proto = [
		['description', str, SANITIZE_CC|SKIP_START_WHITESPACES],
	]


class NetMessageSvVoteSet(NetMessageSv):
	name = 'SvVoteSet'

	attr_proto = [
		['timeout', int],
		['description', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['reason', str, SANITIZE_CC|SKIP_START_WHITESPACES],
	]


class NetMessageSvVoteStatus(NetMessageSv):
	name = 'SvVoteStatus'

	attr_proto = [
		['yes', int],
		['no', str],
		['pass', str],
		['total', str],
	]


class NetMessageClSay(NetMessageCl):
	name = 'ClSay'

	attr_proto = [
		['team', bool],
		['message', str],
	]


class NetMessageClSetTeam(NetMessageCl):
	name = 'ClSetTeam'

	attr_proto = [
		['team', int],
	]


class NetMessageClSetSpectactorMode(NetMessageCl):
	name = 'ClSetSpectactorMode'

	attr_proto = [
		['spectactor_id', int],
	]


class NetMessageClStartInfo(NetMessageCl):
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
	name = 'ClKill'


class NetMessageClEmoticon(NetMessageCl):
	name = 'ClEmoticon'

	attr_proto = [
		['emoticon', int],
	]


class NetMessageClVote(NetMessageCl):
	name = 'ClVote'

	attr_proto = [
		['vote', int],
	]


class NetMessageClCallVote(NetMessageCl):
	name = 'ClCallVote'

	attr_proto = [
		['type', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['value', str, SANITIZE_CC|SKIP_START_WHITESPACES],
		['reason', str, SANITIZE_CC|SKIP_START_WHITESPACES],
	]


NET_MESSAGES = [
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
	NetMessageClSetSpectactorMode,
	NetMessageClStartInfo,
	NetMessageClChangeInfo,
	NetMessageClKill,
	NetMessageClEmoticon,
	NetMessageClVote,
	NetMessageClCallVote,
]


def get_net_message_for(atype):
	try:
		return NET_MESSAGES[atype]
	except IndexError:
		raise IndexError("Unknown NetMessage class")
