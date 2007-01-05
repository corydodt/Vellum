// import Nevow.Athena
// import DeanEdwards

/*
 * Javascript functionality to support the signup page
 */

/* clear the node and replace contents with the text */
function replaceText(node, newText) { // {{{
    /* clear message node */
    while (node.childNodes.length > 0) 
            node.removeChild(node.childNodes[0]);
    var tn = document.createTextNode(newText);
            
    node.appendChild(tn);
} // }}}

Signup.Signup = Nevow.Athena.Widget.subclass('Signup.Signup');
Signup.Signup.methods( // {{{
    function __init__(self, node) { // {{{
        Signup.Signup.upcall(self, '__init__', node);
        DeanEdwards.addEvent(node, 'submit', 
            function processSignup(event) { return self.submit(event) });
    }, // }}}

    function submit(self, event) { // {{{
        event.stopPropagation();
        event.preventDefault();
        var message = self.firstNodeByClass('message');

        var email = self.node.email.value;
        if (email == '')
        {
            replaceText(message, 'Please fill in your email address.');
            return null;
        }

        var password1 = self.node.password1.value;
        var password2 = self.node.password2.value;
        if (password1 == '' || password2 == '')
        {
            replaceText(message, 'Please fill in your new password twice.');
            return null;
        }
        if (password1 != password2)
        {
            replaceText(message, "Passwords don't match! Try again.");
            return null;
        }

        var submit = self.node.signup;
        submit.style['display'] = 'none';
        replaceText(message, 'Sending email. (This may take a minute.)');
        var loading = document.createElement('img');
        loading.setAttribute('src', "/static/loading.gif");
        message.appendChild(loading);

        var d = self.callRemote("processSignup", email, password1);
        d.addCallback(function _(status) {
            replaceText(message, 'An email has been sent to the above address.');
        });
        d.addErrback(function _(failure) {
            replaceText(message, 'An error occurred signing you up.');
            submit.style['display'] = '';
        });
        return d;
    } // }}}
); // }}}

// vi:foldmethod=marker
