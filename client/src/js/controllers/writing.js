/**
 * @ngdoc function
 * @name miller.controller:WritingCtrl
 * @description
 * # DraftCtrl
 * handle saved story writing ;)
 */
angular.module('miller')
  .controller('WritingCtrl', function ($scope, $log, $q, $modal, story, localStorageService, StoryFactory, StoryTagsFactory, StoryDocumentsFactory, CaptionFactory, DocumentFactory, EVENTS, RUNTIME) {
    $log.debug('WritingCtrl welcome', story);

    $scope.isDraft = false;
    $scope.isSaving = false;

    $scope.title = story.title;
    $scope.abstract = story.abstract;
    $scope.contents = story.contents;
    $scope.keywords = _.filter(story.tags, {category: 'keyword'});

    $scope.displayedTags = _.filter(story.tags, function(d){
      return d.category != 'keyword'
    });

    $scope.metadata = {
      status: story.status,
      owner: story.owner
    }

    $scope.setStatus = function(status) {
      $scope.metadata.status = status;
      $scope.save();
    }

    /*
      Save or delete documents according to text contents.
    */
    var documentSlugs =  _.map(story.documents, 'slug');

    $scope.setDocuments = function(documents) {
      // check what to save vs what to discard.
      var saveable = documents.filter(function(d){
        return documentSlugs.indexOf(d.slug) == -1;
      });

      var deletable = documents.filter(function(d){
        return documentSlugs.indexOf(d.slug) == -1;
      });

      var included = _.map(documents, 'slug');

      console.log(documentSlugs)
      $log.log('WritingCtrl -> setDocuments()', documents.length, '- to be saved:', saveable, '- to be deleted:');
      
      documents = story.documents.filter(function(d){
        return included.indexOf(d.slug) != -1
      });

      if(saveable.length || deletable.length){
        $q.all(_.compact(
          saveable.map(function(d) {
            return CaptionFactory.save({
              story: story.id,
              document: d
            }, function(res){
              console.log('saved', res);
              return res
            }).promise
          })
          // .concat(deletable.map(function(d) {
          //   return CaptionFactory.save({
          //     story: story.id,
          //     document: d
          //   }, function(res){
          //     console.log('saved', res);
          //   }).promise
          // }))
        )).then(function(){
          debugger;
          $scope.$parent.setDocuments(documents);
        });
      } else{
        var indexed = _.keyBy(story.documents, 'slug'),
            docs = _(documents).uniq('slug').map(function(d){
              return indexed[d.slug]
            }).value();
        console.log('indexed', docs)

        $scope.$parent.setDocuments(docs);
      }

      

    }

    $scope.references = [];
    $scope.lookups = [];// ref and docs and urls...

    // atthach the tag $tag for the current document.
    $scope.attachTag = function(tag) {
      $log.debug('WritingCtrl -> attachTag() tag', arguments);
      $scope.isSaving = true;
      $scope.lock();
      return StoryFactory.patch({id: story.id}, {
        tags: _.map($scope.displayedTags, 'id')
      }).$promise.then(function(res) {
        $log.debug('WritingCtrl -> attachTag() tag success', res);
        $scope.unlock();
        $scope.isSaving =false;
        return true
      }, function(){
        // error
        return false
      });
    }

    /*
      Detach a tag that was attached before.
    */
    $scope.detachTag = function(tag) {
      $log.debug('WritingCtrl -> detachTag() tag', arguments, $scope.displayedTags);
      $scope.isSaving = true;
      $scope.lock();
      
      return StoryFactory.patch({id: story.id}, {
        tags: _.map($scope.displayedTags, 'id')
      }).$promise.then(function(res) {
        $log.debug('WritingCtrl -> detachTag() tag success', res);
        $scope.unlock();
        $scope.isSaving =false;
        return true
      }, function(){
        // error
        return false
      });
    }

    $scope.suggestReferences = function(service) {
      if(!service)
        DocumentFactory.get(function(){
          console.log('list')
        })
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
  
