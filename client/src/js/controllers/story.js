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
        console.log('StoryCtrl -> setStatus - new status:',res)
        $scope.story.status = res.status;
        $scope.$emit(EVENTS.MESSAGE, 'saved');
        $scope.unlock();
      });
    }


    $scope.download = function() {
      StoryFactory.download({
        id: $scope.story.id
      }).$promise.then(function(result) {
        debugger
        var url = URL.createObjectURL(new Blob([result.data]));
        var a = document.createElement('a');
        a.href = url;
        a.download = result.filename;
        a.target = '_blank';
        a.click();
      })
      .catch(function(error) {
        console.log(error); // in JSON
      });
    }

    $scope.listener = function(event, data, callback) {
      $log.log('StoryCtrl > listener, event:', event, data);
      
      switch(event){
        case EVENTS.MARKDOWNIT_FOCUS:
          // cfr. in service MarkdownitService idx is the item index 
          // of every special link. Each link will then have a special id 'item-N'
          // N revealing the ordering.
          $scope.focusedIdx = data.idx
          break;
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
      $log.log('StoryCtrl > setDocuments items n.:', items.length, items);
      var documents = [];

      $scope.sidedocuments = 0;

      documents = _(items)
        .map(function(d){
          // check if it is in the story.documents list
          for(var i=0;i<story.documents.length;i++){
            if(story.documents[i].slug == d.slug){
              $scope.sidedocuments += !!d.citation.length;
              return angular.extend({
                _type: d._type,
                _index: d._index,
                citation: d.citation
              }, story.documents[i]);
            }
          }

          for(i=0;i<story.stories.length;i++){
            if(story.stories[i].slug == d.slug){
              $scope.sidedocuments += !!d.citation.length;
              return angular.extend({
                _type: d._type,
                _index: d._index,
                citation: d.citation
              }, story.stories[i]);
            }
          }
          $scope.sidedocuments++;
          // this is another story or a footnote or a missing document (weird)
          // will be lazily filled with stuffs later
          return d;
        }).value();

      $log.log('StoryCtrl > setDocuments items n.:', items.length, '- documents n:', documents.length, '- sideDocuments:', $scope.sidedocuments );
        
      // $rootScope.emit(documents = documents;

      $scope.$parent.setDocuments(documents);
    };
  });
  