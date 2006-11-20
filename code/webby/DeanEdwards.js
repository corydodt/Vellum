// written by Dean Edwards, 2005
// with input from Tino Zijdel, Matthias Miller, Diego Perini

// http://dean.edwards.name/weblog/2005/10/add-event/

DeanEdwards.addEvent = function (element, type, handler) {
    if (element.addEventListener) {
        element.addEventListener(type, handler, false);
    } else {
        // assign each event handler a unique ID
        if (!handler.$$guid) handler.$$guid = DeanEdwards.addEvent.guid++;
        // create a hash table of event types for the element
        if (!element.events) element.events = {};
        // create a hash table of event handlers for each element/event pair
        var handlers = element.events[type];
        if (!handlers) {
            handlers = element.events[type] = {};
            // store the existing event handler (if there is one)
            if (element["on" + type]) {
                handlers[0] = element["on" + type];
            }
        }
        // store the event handler in the hash table
        handlers[handler.$$guid] = handler;
        // assign a global event handler to do all the work
        element["on" + type] = DeanEdwards.handleEvent;
    }
};
// a counter used to create unique IDs
DeanEdwards.addEvent.guid = 1;

DeanEdwards.removeEvent = function (element, type, handler) {
    if (element.removeEventListener) {
        element.removeEventListener(type, handler, false);
    } else {
        // delete the event handler from the hash table
        if (element.events && element.events[type]) {
            delete element.events[type][handler.$$guid];
        }
    }
};

DeanEdwards.handleEvent = function (event) {
    var returnValue = true;
    // grab the event object (IE uses a global event object)
    event = event || DeanEdwards.fixEvent(((this.ownerDocument || this.document || this).parentWindow || window).event);
    // get a reference to the hash table of event handlers
    var handlers = this.events[event.type];
    // execute each event handler
    for (var i in handlers) {
        this.$$handleEvent = handlers[i];
        if (this.$$handleEvent(event) === false) {
            returnValue = false;
        }
    }
    return returnValue;
};

DeanEdwards.fixEvent = function (event) {
    // add W3C standard event methods
    event.preventDefault = DeanEdwards.fixEvent.preventDefault;
    event.stopPropagation = DeanEdwards.fixEvent.stopPropagation;
    if (event.target === undefined) event.target = event.srcElement; // CDD
    return event;
};
DeanEdwards.fixEvent.preventDefault = function() {
    this.returnValue = false;
};
DeanEdwards.fixEvent.stopPropagation = function() {
    this.cancelBubble = true;
};
