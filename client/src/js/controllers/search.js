/**
 * @ngdoc function
 * @name miller.controller:searchCtrl
 * @description
 * # searchCtrl
 * template: js/templates/search.html
 */
angular.module('miller')
  .controller('SearchCtrl', function ($scope, $log, items, $stateParams, $location, StoryFactory) {
    $log.debug('SearchCtrl welcome', $stateParams.query);
    
    $scope.count = items.count;
    $scope.items = items.results;
    $scope.query = $stateParams.query;

    $scope.$on('$locationChangeSuccess', function (e, path) {
      $log.debug('SearchCtrl @$locationChangeSuccess', $scope.qs);

      StoryFactory.search(angular.extend({
        q:$scope.query
      }, $scope.qs), function(res) {
        $scope.count = res.count;
        $scope.items = res.results;
      }, function(err){

      });
    });
  });