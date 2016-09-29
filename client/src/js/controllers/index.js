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
    function tokenize(text, maxwords) {
      var words = text.split(/(?!=\.\s)\s/);

      var sentence = _.take(words, maxwords).join(' ');
      if(sentence.length < text.length){
        if(!sentence.match(/\?\!\.$/)){
          sentence += ' '
        }
        
        sentence += '...'
      }
      // console.log(text, sentences);
      return sentence;
    }

    function excerpt(story) {
      story.excerpt = {}
      for(var i in story.metadata.abstract)
        story.excerpt[i] = tokenize(story.metadata.abstract[i], 10)
      return story
    }

    writings.results = writings.results.map(excerpt);

    $scope.coverstory = writings.results.shift();
    $scope.otherstories = writings.results;

    // check cover of coverstory
    if($scope.coverstory && $scope.coverstory.covers.length){
      $scope.coverstory.cover = _.get(_.first($scope.coverstory.covers), 'metadata.thumbnail_url');
    }


    $scope.news = news.results.map(excerpt);
    $log.debug('IndexCtrl welcome',$scope.news);


  });
  