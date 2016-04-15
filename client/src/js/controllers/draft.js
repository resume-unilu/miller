/**
 * @ngdoc function
 * @name miller.controller:DraftCtrl
 * @description
 * # DraftCtrl
 * handle draft writing ;)
 */
angular.module('miller')
  .controller('DraftCtrl', function ($scope, $log, localStorageService, StoryFactory, EVENTS) {
    $log.debug('DraftCtrl welcome');
    
    $scope.isDraft = true;

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

    $scope.$on(EVENTS.SAVE, function() {
      StoryFactory.save({}, angular.extend({
        title: $scope.title,
        abstract: $scope.abstract,
        contents: $scope.contents
      }, $scope.metadata), function(res) {
        console.log(res)
      })
    });

    _offsetables['writing-tools'] = $('#writing-tools');

    /*
      Watch for relevant changes (i;e. trigger after n milliseconds at least)
    */

    $scope.$watch('title', function(title){
      if(title && title.length) {
        console.log('DraftCtrl @title v', title);
        localStorageService.set('title', title);
      }
    });

    $scope.$watch('abstract', function(abstract){
      if(abstract && abstract.length) {
        localStorageService.set('abstract', abstract);
      }
    });

    $scope.$watch('contents', function(contents){
      if(contents && contents.length) {
        localStorageService.set('contents', contents);
      }
    });

    $scope.$watch('metadata', function(metadata){
      if(!_.isEmpty(metadata)) {
        localStorageService.set('metadata', metadata);
      }
    }, true)

    /*
      load from localstorageservice
    */
    $scope.title    = localStorageService.get('title') || '';
    $scope.abstract = localStorageService.get('abstract') || '';
    $scope.contents = localStorageService.get('contents') || '';
    $scope.metadata   = localStorageService.get('metadata') || {
      status: 'draft',
      tags: [],
      authors: []
    };
  });
  