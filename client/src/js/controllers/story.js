/**
 * @ngdoc function
 * @name miller.controller:coreCtrl
 * @description
 * # CoreCtrl
 * common functions go here.
 */
angular.module('miller')
  .controller('StoryCtrl', function ($rootScope, $scope, $log, story, StoryFactory, EVENTS) {
    $scope.story = story;

    // is the story editable by the current user?
    $scope.story.isWritable = $scope.hasWritingPermission($scope.user, $scope.story);

    // is the layout table or other?
    $scope.layout = 'inline';

    // set status DRAFT or PUBLIC to the document.
    $scope.setStatus = function(status){
      $log.debug('StoryCtrl -> setStatus - status:', status);
      
      if(!$scope.user.is_staff)
        return;
        
      $scope.$emit(EVENTS.MESSAGE, 'saving');

      StoryFactory.update({
        id: $scope.story.id
      }, {
        title: $scope.story.title,
        status: status
      }, function(res) {
        $scope.story.status = res.status;
        $scope.$emit(EVENTS.MESSAGE, 'saved');
        $scope.unlock();
      });
    }

    $scope.listener = function(event, data, callback) {
      $log.log('StoryCtrl > listener, event:', event, data);
      
      switch(event){
        case EVENTS.MARKDOWNIT_FULLSIZE:
          $rootScope.fullsize(data.slug.replace(/\//g,'-'), data.type);
          break;
        case EVENTS.MARKDOWNIT_RESOLVE:
          $rootScope.resolve(data.slug.replace(/\//g,'-'), data.type, callback);
          break;
      }
    }


    $log.log('StoryCtrl ready, title:', story.title, 'isWritable:', $scope.story.isWritable);
    // $scope.cover = _(story.documents).filter({type: 'video-cover'}).first();

    // $scope.hasCoverVideo = $scope.cover !== undefined;
    
    // guess if there's a document interview
    // cfr corectrl setDocuments function.
    $scope.setDocuments = function(items) {
      $log.log('StoryCtrl > setDocuments items n.:', items.length);
      var documents = [],
          unlinkeddocument = [];


      documents = _.compact([$scope.cover].concat(items.map(function(item){
        var _docs = story.documents.filter(function(doc){
          return doc.slug == item.slug;
        });

        if(!_docs.length){
          $log.error("StoryCtrl > cant't find any document matching the link:",item.slug);
          return null;
        }
        return angular.extend({
          citation: item.citation
        }, _docs[0]);

      })));

      $scope.$parent.setDocuments(documents.concat(unlinkeddocument));
    };
  });
  