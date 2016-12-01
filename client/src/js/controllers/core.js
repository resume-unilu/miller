/**
 * @ngdoc function
 * @name miller.controller:coreCtrl
 * @description
 * # CoreCtrl
 * common functions go here.
 */
angular.module('miller')
  .controller('CoreCtrl', function ($rootScope, $scope, $log, $location, $window, $anchorScroll, $state, $modal, $alert, localStorageService, $translate, $timeout, StoryFactory, DocumentFactory, TagFactory, RUNTIME, EVENTS) {    
    $log.log('CoreCtrl ready, user:', RUNTIME.user.username, RUNTIME);

    $scope.user = $rootScope.user = RUNTIME.user;
    $scope.settings = RUNTIME.settings;

    $rootScope.page = 'index';

    $scope.hasToC = false;
    $scope.ToCEnabled = false;

    $scope.stopStateChangeStart = false; // cfr toggleStopStateChangeStart below

    $scope.toggleTableOfContents = function() {
      $scope.hasToC = !$scope.hasToC;
    };

    $scope.locationPath = '';

    // toggle stopStateChangeStart variable thus affecting the StateChangeStart event
    $scope.toggleStopStateChangeStart = function(value) {
      $log.debug('CoreCtrl > toggleStopStateChangeStart value:', value, '- current:',$scope.stopStateChangeStart);
      $scope.stopStateChangeStart = typeof value == 'boolean'? value: !$scope.stopStateChangeStart;
    };

    $scope.setToC = function(ToC) {
      $log.log('CoreCtrl > setToC data:', ToC);
      $scope.ToC = ToC;
      // $scope.ToCEnabled = false;
    };

    $scope.disableToC = function(){
      $scope.ToCDisabled = true;
    };

    // search

    $scope.search = function(searchquery){
      $log.log('CoreCtrl > search() searchquery:', searchquery);

      $state.go('search', {
        q: searchquery
      });
    };

    // add document items to the table-of)documents
    $scope.setDocuments = function(documents) {
      $log.log('CoreCtrl > setDocuments items n.:', documents.length, documents);
      $scope.documents = _.uniq(documents, 'id');
      if($scope.qs.view) {
        // check if it's somewhere in the scope, otherwise callit
        for(var i=0,j=$scope.documents.length;i<j;i++){
          if($scope.qs.view == $scope.documents[i].short_url){
            $scope.fullsized = $scope.documents[i];
            fullsizeModal.$promise.then(fullsizeModal.show);
            break;
          }
        }
      }
    };

    // look for document by slug (internal, cached docs or ask for new one)
    $rootScope.resolve = function(slug, type, callback){
      if(type == 'voc'){
        $log.log('CoreCtrl > $scope.resolve [requesting] voc slug:', slug);
        StoryFactory.get({id: slug}, callback);
      } else {
        var matching = $scope.documents.filter(function(d){
          return d.slug == slug;
        });
        if(matching.length){
          $log.log('CoreCtrl > $scope.resolve [cached] doc slug:', slug);
          callback(matching[0]);
        } else {
          $log.log('CoreCtrl > $scope.resolve [requesting] doc slug:', slug);
          DocumentFactory.get({id: slug}, callback);
        }
      }
    };

    $scope.save = function(){
      $log.log('CoreCtrl > @SAVE ...'); 
      $scope.$broadcast(EVENTS.SAVE);
    };

    $scope.download = function(){
      $log.log('CoreCtrl > @DOWNLOAD ...'); 
      $scope.$broadcast(EVENTS.DOWNLOAD);
    };

    $scope.update = function(key, value){
      $log.log('CoreCtrl > @UPDATE ',key,':',value,' ...'); 
      var _d = {};
      _d[key] = value;
      $scope.$broadcast(EVENTS.UPDATE, _d);
    };


    $scope.lock = function(){
      $log.log('CoreCtrl > lock .............'); 
      
    };

    $scope.unlock = function(){
      $log.log('CoreCtrl > unlock .............'); 
      
    };

    /*
      Suggest tags for writing purposes
    */
    $scope.suggestTags = function(query, options) {
      $log.log('CoreCtrl -> suggestTags', query, options);
      var filters = options || {};
      filters.name__icontains = query;
      return TagFactory.get({
        filters: JSON.stringify(filters)
      }).$promise.then(function(response) {
        return response.results;
      });
    };

    /*

    */
    /*
      Set breaking news above the header.
      Cfr indexCtrl
    */
    $scope.breakingNews = [];
    $scope.setBreakingNews = function(breakingNews) {
      $scope.breakingNews = breakingNews.slice(0,2).map(function(d){
        if(d.covers && d.covers.length){
          var cover = d.covers[0];

          d.cover_url = _.get(cover, 'metadata.thumbnail_url') || _.get(cover, 'metadata.urls.Preview') || _.get(cover, 'snapshot') || cover.url;
          
        }
        return d;
      });
    };

    $rootScope.$on('$stateChangeStart', function (e, state) {
      $log.log('CoreCtrl @stateChangeStart new:', state.name, '- previous:', $scope.state);
      // login page
      if(state.name == 'login' && $scope.user.short_url){
        $log.warn('... cannot swithc to login, user already logged in:', $scope.user.username);
        debugger
        e.preventDefault();
        if($scope.state && $scope.state!='login')
          $state.go($scope.state);
        else
          $state.go('index');
        
        return;
      }

      if($scope.stopStateChangeStart === true){
        // check the user has wirtten sometihing..
        var answer = confirm("Are you sure you want to leave this page?");
        if (!answer) {
            e.preventDefault();
        }
      }
    });


    $rootScope.$on('$stateChangeSuccess', function (e, state, stateParams, from, fromParams) {
      var h =  $location.hash();

      // google

      // clean
      $scope.ToC = [];
      $scope.documents = [];

      // the ui.router state (cfr app.js)
      // debugger
      $scope.state = state.name;
      
      $scope.previousState = {
        from: from,
        fromParams: fromParams
      };

      $rootScope.page = _.compact(state.name
        .split('.')
        .filter(function(d){
          return ['page', 'all', 'story'].indexOf(d) ==-1;
        }).concat([ 
        $state.params.name, 
        $state.params.storyId,
        $state.params.postId 
      ])).join(' - ');

      $scope.absoluteUrl = $state.href($state.current.name, $state.params, {
        absolute: true
      });

      $log.debug('CoreCtrl @stateChangeSuccess - name:', state.name, '- page:', $rootScope.page);

      if(h && h.length)
        $timeout($anchorScroll, 0); // wait for the next digest cycle (cfr marked directive)

      // toggle stopChanceStart if the state is among the blocking ones
      $scope.toggleStopStateChangeStart(false);

      // google analytics
      $window.ga('send', 'pageview', $location.path());

    });


    $scope.setHash = function(hash) {
      $location.hash(hash);
    };

    $scope.changeLanguage = function(key) {
      $scope.language = key;
      $rootScope.language = key;
      localStorageService.set('lang', $scope.language);
      $log.log('CoreCtrl -> changeLanguage language:', $scope.language)
      $translate.use(key);
    };

    $scope.isWithoutAuthors = function(story) {
      return story.authors.length !== 0;
    };

    /*
      Check that the user is allowed to write contents for the given story
      (enforced on server side of course)
    */
    $scope.hasWritingPermission = function(user, story) {
      return  !!user.username && 
              user.username.length > 0 && 
              (user.is_staff || story.owner.username == user.username);
    };

    /*
      When requested, fullsize for documents.
      Cfr also locationChangeSuccess listener 
    */
    var fullsizeModal = $modal({
      scope: $scope, 
      template: RUNTIME.static + 'templates/partials/modals/fullsize.html',
      id: 'dii',
      show: false
    });
    
    $scope.$on('modal.hide', function(e,modal){
      if(modal.$id== 'dii')
        $location.search('view', null);
    });

    // 
    $rootScope.fullsize = function(slug, type) {
      $log.log('CoreCtrl -> fullsize, doc slug:', slug, type);
      
      if(type=='voc'){
        $state.go('story', {
          postId:slug
        })
      } else {
        $location.search('view', slug);
      }
      // $scope.fullsized = doc;
      // $location.search('view', doc.short_url);
    };


    /*
      Prevent from closing
    */
    window.onbeforeunload = function (event) {
      if($scope.state && ['draft', 'writing'].indexOf($scope.state) !== -1){
        var message = 'Sure you want to leave?';
        if (typeof event == 'undefined') {
          event = window.event;
        }
        if (event) {
          event.returnValue = message;
        }
        return message;
      }
    };

    /*
      On location change, collect the parameters.
      Since this is called BEFORE statehangeSuccess, the scrolling cannot be made at this level.
    */
    $scope.$on('$locationChangeSuccess', function (e, path) {
      $log.debug('CoreCtrl @locationChangeSuccess', path, $location);
      $scope.qs = $location.search();
      $scope.locationPath = path;
      $scope.path = $location.path();
      $scope.searchquery = $scope.qs.q;
      // load fullsize
      if($scope.qs.view){
        DocumentFactory.get({id: $scope.qs.view}, function(res){
          $scope.fullsized = res;
          fullsizeModal.$promise.then(fullsizeModal.show);
        });
      }

      if($scope.qs.view && $scope.fullsized && $scope.fullsized.short_url == $scope.qs.view){
        // normal behaviour, after fullsize has been called the view param is present in location
        fullsizeModal.$promise.then(fullsizeModal.show);
      } else if(!$scope.qs.view && $scope.fullsized){
         fullsizeModal.hide();
      }
    });

    $scope.setLocationFilter = function(field, value) {
      $location.search(field, value);
    };

    $scope.removeLocationFilter = function(field) {
      $location.search(field, null);
    };

    // watch 400 bad request form error. Cfr app.js interceptors.
    $rootScope.$on(EVENTS.BAD_REQUEST, function(e, rejection){
      $alert({
        placement: 'top',
        title: 'form errors', 
        'animation': 'bounceIn',
        content: _(rejection.data).map(function(d,k){
          return '<div><b>'+k+'</b>: '+d+'</div>';
        }).value().join(''),
        show: true, 
        type:'error'
      });
    });

    var timer_event_message;
    // watch for saving or MESSAGE events
    $scope.$on(EVENTS.MESSAGE, function (e, message) {
      $log.log('CoreCtrl @MESSAGE', message);
      $scope.message = message;
      if(timer_event_message)
        $timeout.cancel(timer_event_message);
      timer_event_message = $timeout(function(){
        $scope.message = null;
      }, 2000);
    });
    /*
      First load
    */
    // load language
    $scope.language = localStorageService.get('lang') || 'en_US';
    $scope.changeLanguage($scope.language);
    // load "huighlights"
    StoryFactory.get({
      filters: JSON.stringify({
        tags__slug: 'top',
        status: 'public'
      })
    }, function(data){
      $log.info('CoreCtrl breaking news loaded', data);
      $scope.setBreakingNews(data.results);
    }); 



  });
  