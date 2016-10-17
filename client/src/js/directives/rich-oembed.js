/**
 * @ngdoc function
 * @name miller.directives:rich-oembed
 * @description
 * # richOembed
 * Rich oembed directive, with autoplay. Includes embedit directive as well.
 */
angular.module('miller')
  .directive('richOembed', function($sce, $log, RUNTIME) {
    return {
      restrict : 'A',
      scope:{
        autoplay: '=',
        oembed: '=',
        cover: '='
      },
      templateUrl: RUNTIME.static + 'templates/partials/directives/rich-oembed.html',
      
      link: function(scope, element, attrs) {
        scope.enabled = false;
        
        $log.log('🍩 rich-oembed ready', scope.cover);
      }
    }
  });
