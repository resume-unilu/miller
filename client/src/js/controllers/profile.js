/**
 * @ngdoc function
 * @name miller.controller:MeCtrl
 * @description
 * # MeCtrl
 * common functions go here.
 */
angular.module('miller')
  .controller('ProfileCtrl', function ($scope, $log, profile, authors) {
    $log.log('ProfileCtrl ready, profile:', profile, authors);
    $scope.profile = profile;
    $scope.authors  = authors.results;
  })