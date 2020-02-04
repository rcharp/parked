function GetAirTableEventClass(sel) {
    var base = '';
    var table = '';
    var selection = '';

    if (sel === 'event'){
        base = document.getElementById('event_base_id').value;
        table = document.getElementById('event_table_name').value;
        selection = 'event';
    }
    else{
        base = document.getElementById(sel.id.replace('table_name', 'base_id')).value;
        table = document.getElementById(sel.id).value;
        selection = document.getElementById(sel.id).getAttribute('data-location');
    }

    var token = '{{ from_token }}';

    if (base === null || table === null){
        return false;
    }
    else{
        $.ajax({
              url: '{{ url_for("user.get_airtable_event_class") }}',
              type: 'POST',
              data: {'base': base, 'table': table, 'token': token},
              success: function(response) {

                  var table_name_inputs = document.getElementsByClassName('airtable-table-name');

                  for (var i=0; i< table_name_inputs.length; i++){
                      table_name_inputs[i].value = table;
                  }

                  if ('events' in response){

                      var airtable_dropdowns = document.getElementsByClassName('airtable');
                      for(var k=0; k < airtable_dropdowns.length; k++){
                          for(var l = 0; l<airtable_dropdowns[k].getElementsByTagName('li').length; l++){
                              airtable_dropdowns[k].removeChild(airtable_dropdowns[k].getElementsByTagName('li')[l]);
                          }
                      }

                      var ul = document.getElementsByClassName('action-import-dropdown');
                      for(var i=0; i < ul.length; i++){

                          var last = (last=Object.keys(response['events']))[last.length-1];
                          var li_name = ul[i].getElementsByTagName('li')[0].getElementsByTagName('a')[0].name;

                          // This is commented out because it deletes all Airtable list items

                          //var lis = ul[i].getElementsByClassName('airtable_list_item');
                          //while (lis[0]) {
                              //lis[0].parentNode.removeChild(lis[0]);

                          //}


                          $.each(response['events'], function (k, v) {
                              var li = document.createElement('li');
                              li.id = 'airtable_list_item';
                              li.classList.add('airtable_list_item');

                              if (v.includes('::')){
                                  var location = ' (Event\'s linked table)';
                              }
                              else{
                                  var location = ' (Event)'
                              }

                              li.innerHTML = '<a tabindex="-1" href="" id="' + k + '" data-valueApp="airtable" data-valueId="event" data-valueItem="' + v + '" data-valueName="' + k + '"' +
                              'title="{{ k }}" name="' + li_name + '" onclick="return SelectActionImportedItem(this);">' +
                              '<img src="../../../../../../../static/assets/images/logos/{{ from_app_name }}.png" class="img-fluid mt-5 mt-lg-0" id="app_image"' +
                              'alt="features" width="25px" style="margin-right:20px"><span class="h5 font-w400">' + v + location + '</span></a>';

                              if (k !== last){
                                  li.innerHTML += '<hr style="margin:0" />';
                              }

                              ul[i].appendChild(li);

                          });
                      }

                      var airtable_event_dropdown = document.getElementsByClassName('airtable-event-dropdown');
                      for(var i=0; i < ul.length; i++){
                          var last = (last=Object.keys(response['events']))[last.length-1];
                          var li_name = '';

                          if (airtable_event_dropdown[i].getElementsByTagName('li').length > 0){
                            li_name = airtable_event_dropdown[i].getElementsByTagName('li')[0].getElementsByTagName('a')[0].name;

                            // This is commented out because it deletes all Airtable list items
                            /*
                            var lis = ul[i].getElementsByClassName('airtable_list_item');
                            while (lis[0]) {
                                lis[0].parentNode.removeChild(lis[0]);

                            }
                            */
                          }
                          else{
                              li_name = 'event_column';
                          }

                          $.each(response['events'], function (k, v) {
                              var li = document.createElement('li');
                              li.id = 'airtable_list_item';
                              li.classList.add('airtable_list_item');

                              var location = '';

                              if (selection === 'event'){
                                  location = ' (Event)';
                              }
                              else if (selection === 'action'){
                                  location = ' (Action)';
                              }
                              else {
                                  location = ' (Additional Action ' + selection + ')';
                              }

                              // This is commented out until I add linked tables
                              /*
                              if (v.includes('::')){
                                  var location = ' (Event\'s linked table)';
                              }
                              else{
                                  var location = ' (Event)'
                              }
                              */

                              li.innerHTML = '<a tabindex="-1" href="" id="' + k + '" data-valueApp="airtable" data-valueId="event" data-valueItem="' + v + '" data-valueName="' + k + '"' +
                              'title="{{ k }}" name="' + li_name + '" onclick="return SelectActionImportedItem(this);">' +
                              '<img src="../../../../../../../static/assets/images/logos/{{ from_app_name }}.png" class="img-fluid mt-5 mt-lg-0" id="app_image"' +
                              'alt="features" width="25px" style="margin-right:20px"><span class="h5 font-w400">' + v + location + '</span></a>';

                              if (k !== last){
                                  li.innerHTML += '<hr style="margin:0" />';
                              }

                              if (!airtable_event_dropdown[i].contains(li)){
                                  airtable_event_dropdown[i].appendChild(li);
                              }

                          });
                      }
                  }
              },
              error: function(xhr) {
                  alert("Either your base ID or table name is invalid. Please try again.");
                //Do Something to handle error
              }
        });
    }
}