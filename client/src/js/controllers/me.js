/**
 * @ngdoc function
 * @name miller.controller:MeCtrl
 * @description
 * # MeCtrl
 * common functions go here.
 */
angular.module('miller')
  .controller('MeCtrl', function ($scope, $log) {
    $log.log('MeCtrl ready, user:', $scope.user);
  });
  