/**
 * @ngdoc function
 * @name miller.directives:lazy
 * @description
 * # marked
 * transform markdown data in miller enhanced datas
 */
angular.module('miller')
  .directive('lazyImage', function ($log) {
    return {
      restrict : 'A',
      link : function(scope, element, attrs) {
        $log.log(':::lazy on ',attrs.src);

        element.addClass('lazy-box').css({
          'background-color': '#B7B2B2',
        }).html('<div class="loading">...</div>')
        
        function wakeup(){
          element.css({
            'background-size': 'cover',
            'background-position': 'center center',
            'background-image': 'url(' + attrs.src + ')'
          });
        }


        wakeup();
      }
    };
  })