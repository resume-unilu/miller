/**
 * @ngdoc function
 * @name miller.controller:UploadCtrl
 * @description
 * # UploadCtrl
 * handle story creation via upload.
 */
angular.module('miller')
  .controller('UploadedCtrl', function ($scope, $log, story) {
    $log.debug('UploadedCtrl welcome', story);
    $scope.story = story
  })