/**
 * @ngdoc service
 * @name miller.services
 * @description
 * # core
 * Resource REST API service Factory.
 */
angular.module('miller')
  /*
    Get a list of stories
  */
  .factory('StoryFactory', function ($resource) {
    return $resource('/api/story/:id/', {},{
      update: {
        method:'PUT'
      }
    });
  })
  /*
    get a list of ralreeady saved document accessible by the user
  */
  // http://localhost:8888/api/document/
  .factory('DocumentFactory', function ($resource) {
    return $resource('/api/document/:id/', {},{
      update: {
        method:'PUT'
      }
    });
  })
  /*
    get static pages
  */
  .factory('PageFactory', function ($http, RUNTIME) {
    return {
      get: function(params) {
        return $http.get(RUNTIME.static + 'pages/' + params.name + '.md');
      }
    }
  })