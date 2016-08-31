/**
 * @ngdoc function
 * @name miller.controller:PageCtrl
 * @description
 * # PageCtrl
 * Ctrl for static contents, delivered in markdown.
 */
angular.module('miller')
  .controller('PageCtrl', function ($scope, $log, page) {
    $log.log('PageCtrl ready', page.status);
    // $scope.post = post;
    $scope.md = page.data;

    // colllect media
    
    // collect h1, h2, h3
  });
  