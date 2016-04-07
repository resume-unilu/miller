/**
 * @ngdoc function
 * @name miller.controller:coreCtrl
 * @description
 * # CoreCtrl
 * common functions go here.
 */
angular.module('miller')
  .controller('PostCtrl', function ($scope, $log, post) {
    $log.log('PostCtrl ready', post);
    $scope.post = post;
    
  });
  