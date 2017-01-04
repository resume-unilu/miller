/**
 * @ngdoc function
 * @name miller.controller:indexCtrl
 * @description
 * # IndexCtrl
 */
angular.module('miller')
  .controller('IndexCtrl', function ($scope, $log, writings, news) {
    $log.debug('IndexCtrl welcome', writings, news);
    $scope.setOG({
      type: 'platform'
    });
    /*
      Get the firs n sentence until the number of words are covered.
      return an array
    */
    function tokenize(text, maxwords) {
      if(!text)
        return "";
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
        story.excerpt[i] = tokenize(story.metadata.abstract[i], 25)
      return story
    }

    writings.results = writings.results.map(excerpt);

    $scope.coverstory = writings.results.shift();
    $scope.otherstories = writings.results;

    // check cover of coverstory
    if($scope.coverstory && $scope.coverstory.covers.length){
      var maincover = _.first($scope.coverstory.covers);
      $scope.coverstory.cover = _.get(maincover, 'metadata.thumbnail_url') || _.get(maincover, 'metadata.attachment');
    }


    $scope.news = news.results.map(excerpt);
    $log.debug('IndexCtrl welcome',$scope.news);


  });
  