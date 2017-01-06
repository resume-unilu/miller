/**
 * @ngdoc function
 * @name miller.controller:indexCtrl
 * @description
 * # IndexCtrl
 */
angular.module('miller')
  .controller('IndexCtrl', function ($scope, $log, $filter, writings, news) {
    $log.debug('IndexCtrl welcome', writings, news);
    $scope.setOG({
      type: 'platform'
    });

    function excerpt(story) {
      story.excerpt = {}
      if(story.tags && story.tags.length && _.filter(story.tags, {slug: 'collection', category:'writing'}).length){
        story.is_collection = true
      }
      for(var i in story.metadata.abstract)
        story.excerpt[i] = $filter('tokenize')(story.metadata.abstract[i], 32)
      return story
    }

    writings.results = writings.results.map(excerpt);

    $scope.coverstory = writings.results.shift();
    $scope.otherstories = writings.results;

    // check cover of coverstory
    if($scope.coverstory && $scope.coverstory.covers.length){
      var maincover = _.first($scope.coverstory.covers);

      $scope.coverstory.cover = _.get(maincover, 'metadata.thumbnail_url') || maincover.snapshot;

    }


    $scope.news = news.results.map(excerpt);
    $log.debug('IndexCtrl welcome',$scope.news);


  });
  