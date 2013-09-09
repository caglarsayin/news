/**
 * Created with PyCharm.
 * User: caglar
 * Date: 08.09.2013
 * Time: 02:55
 * To change this template use File | Settings | File Templates.
 */
$.getJSON('/fetch', function(data) {
  var items = [];
  $.each(data.elements, function(i, item) {items.push('<tr><td><strong>'+ i +'</strong></td><td><span class="glyphicon glyphicon-chevron-up"></span><a href=' + item.uri + 'class="text-news" target="_blank">' + item.quote + '</a> - <abbr title=' + item.uri + 'class="text-muted" style="font-size: 8.5px">' + item.short_uri + '</abbr><p class="text-info" style="font-size: 9px">Puan: ' + item.rate + ' | Ekleyen: ' + item.creator + '| Eklenme tarihi: ' + item.created + '</p></td></tr>');});
  $('#yeniler_body').append(items.join(''));
});