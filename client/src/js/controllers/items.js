/**
 * @ngdoc function
 * @name miller.controller:coreCtrl
 * @description
 * # CoreCtrl
 * common functions go here.
 */
angular.module('miller')
  .controller('ItemsCtrl', function ($scope, $log, items, model, factory) {
    $log.log('ItemsCtrl ready', items);
    $scope.items = items.result;

  });
  