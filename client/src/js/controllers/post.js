/**
 * @ngdoc function
 * @name miller.controller:coreCtrl
 * @description
 * # CoreCtrl
 * common functions go here.
 */
angular.module('miller')
  .controller('PostCtrl', function ($scope, $log, post) {
    $log.log('PostCtrl ready', post);
    $scope.post = post;

    $scope.cover = _(post.documents).filter({type: 'video-cover'}).first();

    $scope.hasCoverVideo = $scope.cover != undefined;
    
    // guess if there's a document interview
    // cfr corectrl setDocuments function.
    $scope.setDocuments = function(items) {
      $log.log('PostCtrl > setDocuments items n.:', items.length);
      var documents = [],
          unlinkeddocument = [];


      documents = _.compact([$scope.cover].concat(items.map(function(item){
        var _docs = post.documents.filter(function(doc){
          return doc.slug == item.slug
        });

        if(!_docs.length){
          $log.error("PostCtrl > cant't find any document matching the link:",item.slug)
          return null;
        }
        return angular.extend({
          citation: item.citation
        }, _docs[0]);

      })))

      $scope.$parent.setDocuments(documents.concat(unlinkeddocument));
    }
  });
  