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
    'ngResource',
    'ngSanitize',
    'ngCookies',
    'angular-medium-editor',
    'mgcrea.ngStrap',
    'monospaced.elastic'
  ])
  .constant('LOCALES', {
    'locales': {
      'en_US': 'English'
    },
    'preferredLocale': 'en_US'
  })
  /*
    Angular-translate configs
    Cfr. https://scotch.io/tutorials/internationalization-of-angularjs-applications
  */
  // .config(function ($translateProvider) {
  //   // $translateProvider.useMissingTranslationHandlerLog();
  //   $translateProvider.useSanitizeValueStrategy('sanitize');
  //   $translateProvider.useStaticFilesLoader({
  //       prefix: 'locale/locale-',// path to translations files
  //       suffix: '.json'// suffix, currently- extension of the translations
  //   });
  //   $translateProvider.preferredLanguage('en_US');// is applied on first load
    
  // })

  .config(function($locationProvider) {
    // $locationProvider.html5Mode(true);
  })
  .config(function ($stateProvider, $urlRouterProvider, RUNTIME) {
    $urlRouterProvider
      .otherwise("/");
    $stateProvider
      .state('index', {
        url: '/',
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
        controller: 'LoginCtrl',
        templateUrl: RUNTIME.static + 'templates/login.html'
      })
      .state('draft', {
        url: '/create',
        controller: 'DraftCtrl',
        templateUrl: RUNTIME.static + 'templates/draft.html'
      })
      .state('me', {
        abstract: true,
        url: '/me',
        controller: 'MeCtrl',
        templateUrl: RUNTIME.static + 'templates/me.html'
      })
        .state('me.stories', {
          url: '/stories',
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
        abstract:true,
        controller: 'BlogCtrl',
        templateUrl: RUNTIME.static + 'templates/blog.html',
        
      })

      .state('blog.everything', {
        url: '',
        controller: 'ItemsCtrl',
        templateUrl: RUNTIME.static + 'templates/blog.news.html',
        resolve: {
          items: function(StoryFactory, $stateParams) {
            return StoryFactory.get({
              filters: JSON.stringify({
                tags__category__in: ['blog'] 
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
      .state('blog.events', {
        url: '/events',
        controller: 'ItemsCtrl',
        templateUrl: RUNTIME.static + 'templates/blog.news.html',
        resolve: {
          items: function(StoryFactory, $stateParams) {
            return StoryFactory.get({
              filters: JSON.stringify({
                tags__category__in: ['blog'] ,
                tags__slug__in: ['event'] 
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
        Three publications
      */
      .state('publications', {
        url: '/publications',
        abstract: true,
        controller: function(){

        },
        templateUrl: RUNTIME.static + 'templates/publications.html',
        
      })
        .state('publications.papers', {
          url: '',
          controller: 'ItemsCtrl',
          templateUrl: RUNTIME.static + 'templates/blog.news.html',
            resolve: {
            items: function(StoryFactory, $stateParams) {
              return StoryFactory.get({
                filters: JSON.stringify({
                  tags__slug: 'paper'
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
        .state('publications.interviews', {
          url: '/interviews',
          controller: 'ItemsCtrl',
          templateUrl: RUNTIME.static + 'templates/blog.news.html',
            resolve: {
            items: function(StoryFactory, $stateParams) {
              return StoryFactory.get({
                filters: JSON.stringify({
                  tags__slug: 'interview'
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



      .state('post', {
        url: '/story/:postId',
        controller: 'PostCtrl',
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
      })
  });
