conditions = { True: lambda a: True }
class MyObject( object ):
	def __repr__( self ):
		return "%s %s" % ( str( self ), super( MyObject, self ).__repr__( ) )

class Modifier( MyObject ):
	def __init__( self, cause, number, conditions, condition=True ):
		self.cause = cause
		self.targets = { }
		self.number = number
		self.conditions = conditions
		self.condition = condition
		self.targetId = None

	def __add__( self, other ):
		number = int( self )
		return number + other
	__radd__ = __add__

	def __int__( self ):
		if self.targetId is None or self.conditions[ self.condition ]( self.target ):
		#If the circumstances are right, add me to the value
			return self.number
		else:
			return 0

	def addTarget( self, target ):
		self.targets[ target.key ] = target
		target.modifiers[ self.key ] = self

	def __str__( self ):
		number = self.number
		return "%s%s ( from %s )" % ( number > -1 and "+" or "", number, str( self.cause ) )

	def addTarget( self, target ):
		self.targets[ target.key ] = target
		target.modifiers[ self.key ] = self

	def addToTargets( self ):
		for target in self.targets.values( ):
			target.modifiers[ self.key ] = self

	def removeFromTargets( self ):
		for target in self.targets.values( ):
			del target.modifiers[ self.key ]

	def removeTarget( self, target ):
		del self.targets[ target.key ]
		del target.modifiers[ self.key ]

	def resolveForTarget ( self, targetId ):
		if targetId not in self.targets:
			targetId = targetId.key
		targ = self.targetId
		self.targetId = targetId
		number = int( self )
		self.targetId = targ
		return number

	#Properties
	def getKey( self ):
		return "%s: %s %s" % ( self.__class__.__name__, getattr( self.cause, 'key', self.cause ), " ".join( self.targets.keys( ) ) )
	key = property( fget=getKey, doc="The unique ke for this Modifier" )
	
	def getTarget( self ):
		return self.targets[ self.targetId ]
	target = property( fget=getTarget, doc="The current target of this modifier" )

	def getNumber( self ):
		return self._number( )

	def setNumber( self, number ):
		self._number = callable( number ) and number or ( lambda: number )

	number = property( fget=getNumber, fset=setNumber, doc="This Attributes base value" )

class Attribute( MyObject ):
	lastkey = 0
	
	def __init__( self, name, number, conditions ):
		self.name = name
		self.number = number
		self.modifiers = { }
		self.key = "%s %s" % ( self.__class__.__name__, self.lastkey )
		Attribute.lastkey += 1
		self.situation = True
		self.conditions = conditions

	def __add__( self, other ):
		return int( self ) + other
	__radd__ = __add__

	def __cmp__( self, other ):
		import math
		diff = self - other
		return diff and diff / math.fabs( diff ) or diff

	def __int__( self ):
		return self.number + sum( self.modifiers.values( ) )

	def __str__( self ):
		return "%s: " % self.name + " ".join( [ "%s" % self.number ] + [ str( mod ) for mod in self.modifiers.values( ) ] ) + " = %s" % int( self )

	def __sub__( self, other ):
		return int( self ) - other
	__rsub__ = __sub__

	def resolveForSituation( self, situation ):
		sit = self.situation
		self.situation = situation
		ammount = int( self )
		self.situation = sit
		return ammount

	#Properties
	def getNumber( self ):
		return self._number( )

	def setNumber( self, number ):
		self._number = callable( number ) and number or ( lambda: number )

	number = property( fget=getNumber, fset=setNumber, doc="This Attributes base value" )

class Stat( Attribute ):
	def __init__( self, name, number, conditions, modprovided=None ):
		super( Stat, self ).__init__( name, number, conditions )
		self.mod = modprovided or self.number

	def applyMods( self ):
		for mod in self.modprovided:
			mod.addToTargets( )

	def revokeMods( self ):
		for mod in self.modprovided:
			mod.removeFromTargets( )

	#Properties
	def getMod( self ):
		return self.modprovided

	def setMod( self, value ):
		try:
			self.modprovided.number = value
		except:
			self.modprovided = Modifier( self, value, self.conditions )
	mod = property( fget=getMod, fset=setMod, doc="The modifier this Stat provides" )

class CharacterMetaclass( type ):
	def __init__( clss, name, bases, dictionary ):
		def generateProperty( attrType, attrTag, attrName ):
			"""
			Because lambdas do not rememebr their scope, if the stack is overwritten.
			"""
			return ( lambda self: self.attrs[ attrTag ] ), ( lambda self, value: attrType( self, attrTag, attrName, value ) )

		for attrTag, ( attrType, attrName ) in clss.attTypes.items( ):
			get, set = generateProperty( attrType, attrTag, attrName )
			prop = property( fget=get, fset=set, doc="This character's %s scor" % attrName )
			setattr( clss, attrTag, prop )
		super( CharacterMetaclass, clss ).__init__( clss, name, bases, dictionary )

class Character( MyObject ):
	lastkey = 0

	def __init__( self, name, conditions, attrs=None ):
		self.name = name
		self.conditions = conditions
		self.attrs = { }
		self.key = "%s %s" % ( self.__class__.__name__, self.lastkey )
		Character.lastkey += 1
		self.setAttrs( attrs or { } )
		self.setSystemAttrs( )

	def setAttrs( self, attrs ):
		classattrs = dict.fromkeys( self.attTypes, 0 )
		classattrs.update( attrs )
		for name, attr in classattrs.items( ):
			setattr( self, name, attr )

	def setSystemAttrs( self ):
		"""
		Set the attributes that are specific to the system.  Since this is generic, we'll pass
		"""
		pass

	def __str__( self ):
		return "%s\n\t%s\n" % ( self.name, "\n\t".join( [ str( attr ) for attr in self.attrs.values( ) ] ) )

	#Properties
	def setStat( self, tag, name, number, modprovided=None ):
		try:
			self.attrs[ tag ].number = number
		except:
			self.attrs[ tag ] = Stat( name, number, self.conditions, modprovided )

	def setAttribute( self, tag, name, number ):
		try:
			self.attrs[ tag ].number = number
		except:
			self.attrs[ tag ] = Attribute( name, number, self.conditions )

	attTypes = { }
	__metaclass__ = CharacterMetaclass

if __name__ == "__main__":
	import math
	STR = Stat( "Strength", 14, conditions )
	bob = Character( "Bob", conditions )
