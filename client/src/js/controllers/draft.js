/**
 * @ngdoc function
 * @name miller.controller:DraftCtrl
 * @description
 * # DraftCtrl
 * handle draft writing ;)
 */
angular.module('miller')
  .controller('DraftCtrl', function ($scope, $log) {
    $log.debug('DraftCtrl welcome');

    $scope.contents = ""// from markdown
    $scope.mediumOptions = {
      autoLink: true,
      toolbar:{
        buttons: ['bold', 'italic','h2','h3','quote','anchor','orderedlist', 'unorderedlist']
      },
    	extensions: {
    		markdown: new MeMarkdown(function (md) {
               $scope.markdown = md;
               // socketizza socketizza che é meglio
            })
        }
    }
  });
  