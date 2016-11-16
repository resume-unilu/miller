/**
 * @ngdoc function
 * @name miller.controller:DraftCtrl
 * @description
 * # DraftCtrl
 * handle draft writing ;)
 */
angular.module('miller')
  .controller('DraftCtrl', function ($scope, $log, $state, localStorageService, StoryFactory, EVENTS) {
    $log.debug('DraftCtrl welcome');
    
    $scope.isDraft = true;
    $scope.isSaving = false;

    $scope.tags = [];

    $scope.save = function(){
      $log.log('DraftCtrl -> save()')
      if($scope.isSaving){
        $log.warn(' .. is still saving, be patient.')
        return;
      }
      $scope.isSaving = true;
      StoryFactory.save({}, {
        title: $scope.title,
        abstract: $scope.abstract,
        contents: $scope.contents,
        status: 'draft',
        tags: _.map($scope.tags, 'id')
      }, function(res) {
        $scope.isSaving = false;
        $scope.$emit(EVENTS.MESSAGE, 'saved');
        $log.log('DraftCtrl -> @EVENTS.SAVE saved:', res);
        // handle redirection.
        $state.go('writing', {
          storyId: res.id
        });
        // debugger
      }, function(){
        $scope.isSaving = false;
      });
    };
    
    $scope.$on(EVENTS.SAVE, function() {
      $scope.$emit(EVENTS.MESSAGE, 'saving');
      $scope.save();
    });

    // handle attach tag
    $scope.attachTag = function(tag) {
      $log.log('DraftCtrl -> attachTag', tag);
      $scope.tags.push(tag);
    };

    // handle delete tad
    $scope.detachTag = function(tag) {
      $log.log('DraftCtrl -> detachTag', tag);
      // get indexOf current tag
      for(var i=0,j=$scope.tags.length;i<j;i++){
        if($scope.tags[i].id == tag.id){
          $scope.tags.splice(i, 1);
          break;
        }
      }
      // $log.log($scope.tags)
    };

    _offsetables['writing-tools'] = $('#writing-tools');

    /*
      Watch for relevant changes (i;e. trigger after n milliseconds at least)
    */

    // $scope.$watch('title', function(title){
    //   if(title && title.length) {
    //     console.log('DraftCtrl @title v', title);
    //     localStorageService.set('title', title);
    //   }
    // });

    // $scope.$watch('abstract', function(abstract){
    //   if(abstract && abstract.length) {
    //     localStorageService.set('abstract', abstract);
    //   }
    // });

    // $scope.$watch('contents', function(contents){
    //   if(contents && contents.length) {
    //     localStorageService.set('contents', contents);
    //   }
    // });

    // $scope.$watch('metadata', function(metadata){
    //   if(!_.isEmpty(metadata)) {
    //     localStorageService.set('metadata', metadata);
    //   }
    // }, true);

    /*
      load from localstorageservice
    */
    // $scope.title    = localStorageService.get('title') || '';
    // $scope.abstract = localStorageService.get('abstract') || '';
    // $scope.contents = localStorageService.get('contents') || '';
    // $scope.metadata   = localStorageService.get('metadata') || {
    //   status: 'draft',
    //   tags: [],
    //   authors: []
    // };
  });
  