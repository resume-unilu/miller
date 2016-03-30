/**
 * @ngdoc function
 * @name miller.controller:indexCtrl
 * @description
 * # IndexCtrl
 */
angular.module('miller')
  .controller('IndexCtrl', function ($scope, $log, lastItems) {
    $log.debug('IndexCtrl welcome', lastItems);

    $scope.setBreakingNews(lastItems.results);
  });
  