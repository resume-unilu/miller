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
      },
      patch: {
        method:'PATCH'
      }
    });
  })
  .factory('StoryTagsFactory', function ($resource) {
    return $resource('/api/story/:id/tags/', {},{
      update: {
        method:'PUT'
      }
    });
  })
  .factory('StoryDocumentsFactory', function ($resource) {
    return $resource('/api/story/:id/documents/', {},{
      update: {
        method:'PUT'
      }
    });
  })
  .factory('ProfileFactory', function ($resource) {
    return $resource('/api/profile/:username/', {},{
      update: {
        method:'PUT'
      },
      patch: {
        method:'PATCH'
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
  .factory('CaptionFactory', function ($resource) {
    return $resource('/api/caption/:id/', {},{
      update: {
        method:'PUT'
      },
      patch: {
        method:'PATCH'
      }
    });
  })
  /*
    list tags
  */
  .factory('TagFactory', function ($resource) {
    return $resource('/api/tag/:id/', {},{
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
    };
  })

  /*
    Apply MLA or other citation style
  */
  .service('bibtexService', function($filter) {
    return function(json){

    }
  })
  /*
    Apply marked service for custom markdown ;)
  */
  .service('markedService', function($filter) {
    return function(value, language){
      var renderer = new marked.Renderer(),
          linkIndex = 0,
          result = '',
          ToC = [],
          docs = [];

      // split value according to language(reduce pairs)
      if(language){
        var candidate = _(value.split(/<!--\s*(lang:[a-zA-Z_]{2,5})\s*-->/))
          .compact()
          .chunk(2)
          .fromPairs()
          .value();
        // console.log(language, candidate)
        if(candidate['lang:'+language]) {
          value = candidate['lang:'+language];
        }
        //value = value.split();
      }
      // collect h1,h2, hn and get the table of contents ToC
      renderer.heading = function(text, level){
        var h = {
          text: text,
          level: level,
          slug: $filter('slugify')(text)
        };

        ToC.push(h);

        return '<h' + level + '><div class="anchor-sign" ng-click="hash(\''+ h.slug +'\')"><span class="icon-link"></span></div><a name="' + h.slug +'" class="anchor" href="#' + h.slug +'"><span class="header-link"></span></a>' + 
          text + '</h' + level + '>';
      };

      // collect miller document
      renderer.link = function(url, boh, text) {
        if(url.trim().indexOf('doc/') === 0){
          var documents = url.trim().replace('doc/','').split(',');
          for(var i in documents){
            docs.push({
              _index: 'link-' + (linkIndex++), // internal id
              citation: text,
              slug: documents[i]
            });
          }
          return '<a name="' + documents[0] +'" ng-click="hash(\''+url+'\')"><span class="anchor-wrapper"></span>'+text+'</a>';
        } else if (url.trim().indexOf('voc/') === 0){
          var terms = url.trim().replace('voc/','').split(',');
          for(var i in terms){
            docs.push({
              _index: 'link-' + (linkIndex++), // internal id
              citation: text,
              slug: terms[i],
              type: 'glossary'
            });
          }
          return '<a class="glossary" name="' + terms[0] +'" ng-click="hash(\''+url+'\')"><span class="anchor-wrapper"></span>'+text+' <span class="icon icon-arrow-right-circle"></span></a>';
        
        }
        return '<a href='+url+'>'+text+'</a>';
      };

      renderer.image = function(src, title, alt){
        if((alt||'').indexOf('profile/') === 0){
          return '<div class="profile-thumb" style="background-image:url('+src+')"></div>';
        }
        return '<img src="'+ src+ '" title="'+title+'" alt="'+alt+'"/>';
      };

      // get the new documents and save them in background if needed.
      result = marked(value, {
        renderer: renderer
      });

      return {
        html: result,
        ToC: ToC,
        docs: docs
      };
    }; 
  });