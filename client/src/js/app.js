/**
 * @ngdoc overview
 * @name miller
 * @description
 * # miller
 *
 * Main module of the application.
 */
angular
  .module('miller', [
    'ui.router',
    // 'ngAnimate',
    'ngResource',
    'ngSanitize',
    'ngCookies',
    'ngTagsInput',
    'mgcrea.ngStrap',
    'monospaced.elastic',
    'LocalStorageModule',
    'pascalprecht.translate',
    // 'angular-embedly',
    'angular-embed'
  ])
  .constant('LOCALES', {
    'locales': {
      'en_US': 'English'
    },
    'preferredLocale': 'en_US'
  })
  .constant('EVENTS', {
    'SAVE': 'save',
    'MESSAGE': 'message',
    'BAD_REQUEST':'bad_request'
  })
  /*
    multiple input tags configuration
  */
  .config(function(tagsInputConfigProvider, RUNTIME){
    tagsInputConfigProvider
    .setDefaults('tagsInput', {
      replaceSpacesWithDashes:false,
      template: RUNTIME.static + 'templates/partials/tag.input.html' 
    })
    .setDefaults('autoComplete', {
      loadOnDownArrow: true
    });
  })
  /*
    Angular-translate configs
    Cfr. https://scotch.io/tutorials/internationalization-of-angularjs-applications
  */
  .config(function ($translateProvider, RUNTIME) {
    // $translateProvider.useMissingTranslationHandlerLog();
    $translateProvider.useSanitizeValueStrategy('sanitize');
    $translateProvider.useStaticFilesLoader({
        prefix: RUNTIME.static + 'locale/locale-',// path to translations files
        suffix: '.json'// suffix, currently- extension of the translations
    });
    $translateProvider.preferredLanguage('en_US');// is applied on first load
    
  })
  .config(function (localStorageServiceProvider) {
    localStorageServiceProvider
      .setPrefix('miller');
  })
  .config(function($resourceProvider) {
    $resourceProvider.defaults.stripTrailingSlashes = false;
  })
  .config(function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

    // intercept BAD request errors
    $httpProvider.interceptors.push(function($q, $rootScope, EVENTS) {
      return {
        responseError: function(rejection) {
          // emit on 400 error (bad request, mostly form errors)
          if(rejection.status == 400){
            $rootScope.$emit(EVENTS.BAD_REQUEST, rejection);
          }
          return $q.reject(rejection);
        }
      };
    });
  })
  .config(function($locationProvider) {
    // $locationProvider.html5Mode(true);
  })
  .config(function ($stateProvider, $urlRouterProvider, RUNTIME) {
    $urlRouterProvider
      .otherwise("/");
    $stateProvider
      .state('index', {
        url: '/',
        reloadOnSearch : false,
        controller: 'IndexCtrl',
        templateUrl: RUNTIME.static + 'templates/index.html',
        resolve:{
          writings: function(StoryFactory){
            return StoryFactory.get({
              filters: JSON.stringify({
                tags__category: 'writing'
                
              })
            }).$promise;
          },
          news: function(StoryFactory){
            return StoryFactory.get({
              filters: JSON.stringify({
                tags__category: 'blog'
              })
            }).$promise;
          } 
        }
      })
      .state('login', {
        url: '/login',
        reloadOnSearch : false,
        controller: 'LoginCtrl',
        templateUrl: RUNTIME.static + 'templates/login.html'
      })
      .state('draft', {
        url: '/create',
        reloadOnSearch : false,
        controller: 'DraftCtrl',
        templateUrl: RUNTIME.static + 'templates/draft.html'
      })
      .state('writing', {
        url: '/writing/:storyId',
        reloadOnSearch : false,
        controller: 'WritingCtrl',
        templateUrl: RUNTIME.static + 'templates/draft.html',
        resolve: {
          story: function(StoryFactory, $stateParams) {
            return StoryFactory.get({id: $stateParams.storyId}).$promise;
          },
        }
      })
      .state('me', {
        abstract: true,
        reloadOnSearch : false,
        url: '/me',
        controller: 'MeCtrl',
        templateUrl: RUNTIME.static + 'templates/me.html'
      })
        .state('me.stories', {
          url: '/stories',
          reloadOnSearch : false,
          controller: 'ItemsCtrl',
          templateUrl: RUNTIME.static + 'templates/me.stories.html',
          resolve: {
            items: function(StoryFactory) {
              return StoryFactory.get().$promise;
            },
            model: function() {
              return 'story';
            },
            factory: function(StoryFactory) {
              return StoryFactory;
            }
          }
        })

      .state('blog', {
        url: '/blog',
        reloadOnSearch : false,
        abstract:true,
        controller: 'BlogCtrl',
        templateUrl: RUNTIME.static + 'templates/blog.html',
        
      })

      .state('blog.everything', {
        url: '',
        reloadOnSearch : false,
        controller: 'ItemsCtrl',
        templateUrl: RUNTIME.static + 'templates/blog.news.html',
        resolve: {
          items: function(StoryFactory, $stateParams) {
            return StoryFactory.get({
              filters: JSON.stringify({
                tags__category: 'blog'
              })
            }).$promise;
          },
          model: function() {
            return 'story';
          },
          factory: function(StoryFactory) {
            return StoryFactory;
          }
        }
      })
      
      .state('events', {
        url: '/events',
        abstract:true,
        reloadOnSearch : false,
        // controller: function(){},
        templateUrl: RUNTIME.static + 'templates/events.html',
        
      })

      .state('events.everything', {
        url: '',
        controller: 'ItemsCtrl',
        reloadOnSearch : false,
        templateUrl: RUNTIME.static + 'templates/blog.news.html',
        resolve: {
          items: function(StoryFactory, $stateParams) {
            return StoryFactory.get({
              filters: JSON.stringify({
                tags__category: 'event'
              })
            }).$promise;
          },
          model: function() {
            return 'story';
          },
          factory: function(StoryFactory) {
            return StoryFactory;
          }
        }
      })

      /*
        Kind of story:writings publications
      */
      .state('publications', {
        url: '/publications',
        abstract: true,
        reloadOnSearch : false,
        controller: function($scope){
          $scope.urls = RUNTIME.stories.writing;
        },
        templateUrl: RUNTIME.static + 'templates/publications.html',
        
      });

      _.each(RUNTIME.stories.writing, function(d){
        $stateProvider
          .state('publications.' + d.name, {
            url: d.url,
            controller: 'ItemsCtrl',
            templateUrl: RUNTIME.static + 'templates/blog.news.html',
              resolve: {
              items: function(StoryFactory, $stateParams) {
                return StoryFactory.get({
                  filters: d.slug? JSON.stringify({
                    tags__category: 'writing',
                    tags__slug: d.slug
                  }): JSON.stringify({
                    tags__category: 'writing'
                  })
                }).$promise;
              },

              model: function() {
                return 'story';
              },
              factory: function(StoryFactory) {
                return StoryFactory;
              }
            }
          });
      });
      


    $stateProvider
      .state('post', {
        url: '/story/:postId',
        controller: 'PostCtrl',
        reloadOnSearch : false,
        templateUrl: RUNTIME.static + 'templates/post.html',
        resolve: {
          post: function(StoryFactory, $stateParams) {
            return StoryFactory.get({id: $stateParams.postId}).$promise;
          },
        }
      })


      /*
        All the rest are static pages and will download the md files directly
      */
      .state('page', {
        url: '/:name',
        controller: 'PageCtrl',
        templateUrl: RUNTIME.static + 'templates/md.html',
        resolve: {
          page: function(PageFactory, $stateParams) {
            return PageFactory.get({name: $stateParams.name});
          },
        }
      });
  });
