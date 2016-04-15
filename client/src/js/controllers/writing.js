/**
 * @ngdoc function
 * @name miller.controller:WritingCtrl
 * @description
 * # DraftCtrl
 * handle saved story writing ;)
 */
angular.module('miller')
  .controller('WritingCtrl', function ($scope, $log, story, localStorageService, StoryFactory, EVENTS) {
    $log.debug('WritingCtrl welcome', story);

    $scope.isDraft = false;
    $scope.isSaving = false;

    $scope.title = story.title
    $scope.abstract = story.abstract
    $scope.contents = story.contents
    $scope.metadata = {
      status: story.status,
      owner: story.owner
    }

    $scope.setStatus = function(status) {
      $scope.metadata.status = status;
      $scope.save();
    }

    $scope.mediumOptions = {
      autoLink: true,
      // toolbar:{
      //   buttons: ['bold', 'italic','h2','h3','quote','anchor','orderedlist', 'unorderedlist']
      // },
      extensions: {
        markdown: new MeMarkdown(function (md) {
               $scope.markdown = md;
               // localStorageService.set('contents', 'Add this!');
               // console.log(md)
               // socketizza socketizza che é meglio
        })
      }
    }

    $scope.save = function() {
      $log.debug('WritingCtrl @SAVE');
      $scope.isSaving = true;
      $scope.lock();
      StoryFactory.update({id: story.id}, angular.extend({
        title: $scope.title,
        abstract: $scope.abstract,
        contents: $scope.contents
      }, $scope.metadata), function(res) {
        console.log(res)
        $scope.unlock();
        $scope.isSaving =false;
      })
    };

    $scope.$on(EVENTS.SAVE, $scope.save);

    $scope.$watch('contents', function(v){
      console.log('changed contents')
    })
  });
  
