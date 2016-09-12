/**
 * @ngdoc function
 * @name miller.controller:indexCtrl
 * @description
 * # IndexCtrl
 */
angular.module('miller')
  .controller('IndexCtrl', function ($scope, $log, writings, news) {
    $log.debug('IndexCtrl welcome', writings, news);

    /*
      Get the firs n sentence until the number of words are covered.
      return an array
    */
    function tokenize(text, words){
      var sentences = text.split(/[\.!\?]/);
      // console.log(text, sentences);
      return sentences;
    }

    writings.results = writings.results.map(function(d) {
      d.excerpt = d.metadata.abstract[$scope.language]? tokenize(d.metadata.abstract[$scope.language], 10)[0]: '';
      return d;
    });

    $scope.coverstory = writings.results.shift();
    $scope.otherstories = writings.results;

    // check cover of coverstory
    if($scope.coverstory && $scope.coverstory.covers.length){
      $scope.coverstory.cover = _.get(_.first($scope.coverstory.covers), 'metadata.thumbnail_url');
    }


    $scope.news = news.results.map(function(d) {
      d.excerpt = d.metadata.abstract[$scope.language]? tokenize(d.metadata.abstract[$scope.language], 10)[0]: '';
      return d;
    });
    $log.debug('IndexCtrl welcome',$scope.news);


  });
  