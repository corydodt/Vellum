<map version="0.7.1">
<node TEXT="vellum">
<node TEXT="server" POSITION="right">
<node TEXT="forward presence info"/>
<node TEXT="store files"/>
<node TEXT="open http port"/>
<node TEXT="open pb port"/>
<node TEXT="implement irc bot"/>
<node TEXT="Character Model">
<icon BUILTIN="messagebox_warning"/>
</node>
</node>
<node TEXT="client" POSITION="right">
<node TEXT="display map images">
<node TEXT="cached"/>
<node TEXT="multiple, in tabs">
<icon BUILTIN="help"/>
</node>
</node>
<node TEXT="drawing tools for whiteboard"/>
<node TEXT="play sounds"/>
<node TEXT="display chat info - FIXME - irc client?" FOLDED="true">
<icon BUILTIN="button_cancel"/>
<node TEXT="available channels"/>
<node TEXT="available users"/>
<node TEXT="roles of each user"/>
</node>
<node TEXT="chat I/O - FIXME irc client">
<icon BUILTIN="button_cancel"/>
</node>
</node>
<node TEXT="protocol" POSITION="right">
<node TEXT="chat - FIXME, IRC" FOLDED="true">
<icon BUILTIN="button_cancel"/>
<node TEXT="most chat features are client-side plugins">
<node TEXT="markup? HTML.."/>
<node TEXT="rp&apos;ing"/>
<node TEXT="dice"/>
</node>
<node TEXT="prv msgs."/>
</node>
<node TEXT="file tx">
<node TEXT="maps"/>
<node TEXT="sound fx"/>
<node TEXT="music"/>
<node TEXT="icons"/>
<node TEXT="player handouts"/>
</node>
<node TEXT="file rx">
<node TEXT="all of tx, in reverse, for DM to prep server"/>
</node>
<node TEXT="focus updates">
<node TEXT="&quot;Hey, look over here!&quot; - on a map"/>
<node TEXT="or flip to a tab showing a player handout"/>
</node>
<node TEXT="token movements"/>
</node>
<node TEXT="roles" FOLDED="true" POSITION="right">
<node TEXT="DM">
<node TEXT="chat to anyone"/>
<node TEXT="control role +- voice"/>
<node TEXT="kick/ban"/>
<node TEXT="upload maps"/>
<node TEXT="upload sfx"/>
<node TEXT="upload music"/>
<node TEXT="trigger maps, sfx, music to clients"/>
<node TEXT="assign control of tokens"/>
<node TEXT="edit fog"/>
<node TEXT="change focus">
<node TEXT="attention on a particular area of map"/>
<node TEXT="swap to new map"/>
</node>
</node>
<node TEXT="Player">
<node TEXT="chat to anyone when players have voice"/>
<node TEXT="control assigned tokens"/>
<node TEXT="relinquish control of tokens"/>
<node TEXT="upload small sfx"/>
<node TEXT="upload token images"/>
<node TEXT="use whiteboard"/>
</node>
<node TEXT="Lurker">
<node TEXT="chat to anyone when lurkers have voice"/>
</node>
</node>
<node TEXT="questions?" POSITION="right">
<node TEXT="should sounds be localized? (3d)">
<edge WIDTH="thin"/>
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
</node>
</map>
