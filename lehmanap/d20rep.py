from rep import *

class D20AbilityScore( Stat ):
	def __init__( self, name, number, conditions ):
		import math
		super( D20AbilityScore, self ).__init__( name, number, conditions )
		self.mod = lambda: int( math.floor( ( int( self ) - 10 ) / 2 ) )

class D20Character( Character ):

	def setSystemAttrs( self ):
		self.DEX.mod.addTarget( self.AC )

	#Properties
	def setAbilityScore( self, tag, name, number, modsprovided=None ):
		try:
			self.attrs[ tag ].number = number
		except:
			self.attrs[ tag ] = D20AbilityScore( name, number, self.conditions )

	attTypes = { 
				'DEX' : ( setAbilityScore, 'Dexterity' ),
				'AC' : ( Character.setAttribute, 'Armor Class' )
				}

if __name__ == "__main__":
	bob = D20Character( "Bob", conditions )
	dexmod = Modifier( "Cause", 2, conditions )
	print bob.AC
	dexmod.addTarget( bob.DEX )
	print bob.AC
