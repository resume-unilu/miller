/**
 * @ngdoc function
 * @name miller.controller:coreCtrl
 * @description
 * # CoreCtrl
 * common functions go here.
 */
angular.module('miller')
  .controller('StoryCtrl', function ($scope, $log, story) {
    $log.log('StoryCtrl ready', story, $scope.user);
    $scope.story = story;

    // is the story editable by the current user?
    $scope.story.isWritable = $scope.hasWritingPermission($scope.user, $scope.story);

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
  