angular.module('miller')
  .controller('CoversModalCtrl', function ($scope, $log, QueryParamsService, DocumentFactory) {
    /*
      Its scope has read access to:

      $scope.story.covers
      $scope.user

      initialize this modal with a $scope.setTab() that sets the default tab
    */
    $log.info('CoversModalCtrl ready with crazy scope, n. covers:', $scope.story.covers.length);
    /*
      different tabs have different suggest ;)
    */
    $scope.tabs = {
      favourite: {
        name: 'favourite',
        items: [],
        count: 0,
        next: undefined,
        isLoadingNextItems: false,
        suggest: function(query, isNextPage){
          var $s = this;
          $log.debug('CoversModalCtrl - tab.favourite > suggest', $s);
          $s.isLoadingNextItems = true;
          if(!isNextPage){
            $s.next = undefined;
          }

          DocumentFactory.get($s.next || {
            filters: JSON.stringify(query.length > 2? {
              caption__story__owner__username: $scope.user.username,
              contents__icontains: query
            }: {
              caption__story__owner__username: $scope.user.username
            })
          }, function(res){
            $log.debug('CoversModalCtrl - tab.favourite > suggest loaded n.docs:', res.results.length, '- total:', res.count, '-filters:', QueryParamsService(res.next || ''));
            
            $s.items   = $s.next? ($s.items || []).concat(res.results): res.results;
            $s.count   = res.count;
            $s.missing = res.count - $s.items.length;
            $s.next    = QueryParamsService(res.next || '');

            $s.isLoadingNextItems = false;
          });
        },
        init: function(){
          $log.debug('CoversModalCtrl - tab.favourite > init');
          this.suggest($scope.query || '');
        }
      },
      all: {
        name: 'all',
        items: [],
        count: 0,
        next: undefined,
        isLoadingNextItems: false,
        suggest: function(query, isNextPage){
          var $s = this;
          $log.debug('CoversModalCtrl - tab.all > suggest', $s);
          $s.isLoadingNextItems = true;
          if(!isNextPage){
            $s.next = undefined;
          }

          DocumentFactory.get($s.next || {
            filters: JSON.stringify(query.length > 2? {
              contents__icontains: query
            }: {
            })
          }, function(res){
            $log.debug('CoversModalCtrl - tab.all > suggest loaded n.docs:', res.results.length, '- total:', res.count, '-filters:', QueryParamsService(res.next || ''));
            
            $s.items   = $s.next? ($s.items || []).concat(res.results): res.results;
            $s.count   = res.count;
            $s.missing = res.count - $s.items.length;
            $s.next    = QueryParamsService(res.next || '');

            $s.isLoadingNextItems = false;
          });
        },
        init: function(){
          $log.debug('CoversModalCtrl - tab.all > init');
          this.suggest($scope.query || '');
        }
      }
    }

    $scope.selectDocument = function(doc){
      $log.debug('CoversModalCtrl -> selectDocument() id:', doc.id);

      if($scope.selectedDocument && $scope.selectedDocument.id == doc.id){
        // $log.log('::mde -> selectDocument() unselecting previous', doc.url);
        $scope.isSomethingSelected = false;
        $scope.selectedDocument = false;
      } else {
        $scope.isSomethingSelected = true;
        $scope.selectedDocument = angular.copy(doc);
      }
    };

    $scope.addDocument = function() {
      if(!$scope.selectedDocument) {
        $log.warn('CoversModalCtrl -> addDocument() no document has been selected');
        return;
      }
      
      $log.debug('CoversModalCtrl -> addDocument() id:', $scope.selectedDocument.id);

      $scope.setCover($scope.selectedDocument);
      // parent function add Cove
    }

  // http://localhost:8000/api/document/?filters=%7B%22caption__story__owner__username%22%3A%22danieleguido%22%7D&limit=4&offset=4
    $scope.setTab = function(tabname){
      $log.debug('CoversModalCtrl -> setTab() tab.name:', tabname);

      $scope.tab = $scope.tabs[tabname];
      $scope.tab.init()
    }

    // according to current $scope.tab. Cfr. $scope.setTab() methid.
    $scope.suggest = function(query){
      $log.debug('CoversModalCtrl -> suggest() q:', query);
      $scope.tab.suggest(query);
    }

    $scope.more = function(query, tab){
      $log.debug('CoversModalCtrl -> more()');
      $scope.tab.suggest(query, true);
    }

    

    // on init: set the default tab (with init methid called).
    $scope.setTab('favourite');

  })