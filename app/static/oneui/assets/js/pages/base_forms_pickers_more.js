/*
 *  Document   : base_forms_pickers_more.js
 *  Author     : pixelcave
 *  Description: Custom JS code used in Form Pickers and More Page
 */

var BaseFormPickersMore = function() {
    // Init jQuery AutoComplete example, for more examples you can check out https://github.com/Pixabay/jQuery-autoComplete
    var initAutoComplete = function(){
        // Init autocomplete functionality
        jQuery('.js-autocomplete').autoComplete({
            minChars: 1,
            source: function(term, suggest){
                term = term.toLowerCase();

                var $apps  = ['Dropbox','Evernote','Facebook','Gmail','Google Docs','Google Drive','MailChimp','Slack','Trello','Twitter'];
                var $suggestions    = [];

                for ($i = 0; $i < $apps.length; $i++) {
                    if (~ $apps[$i].toLowerCase().indexOf(term)) $suggestions.push($apps[$i]);
                }

                suggest($suggestions);
            }
        });
    };

    return {
        init: function () {
            // Init jQuery AutoComplete example
            initAutoComplete();
        }
    };
}();

// Initialize when page loads
jQuery(function(){ BaseFormPickersMore.init(); });
