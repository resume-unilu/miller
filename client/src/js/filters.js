angular.module('miller')
  .filter('prefixTemplate', function (RUNTIME) {
    return function (input) {
      return RUNTIME.static + input;
    };
  })
  .filter('bibtex', function(){
    return function (text) {
      return text? text.replace(/[\{\}]/g,''): '';
    };
  })
  /*
    Translit non ascii chars and uniform punctuations signs
  */
  .filter('slugify', function(){
    return function (text) {
      var strip  = /[^\w\s-]/g,
          hyphen = /[-\s]+/g,
          slug   = text.toLowerCase();

      var map = {
        from: 'àáäãâèéëêìíïîòóöôõùúüûñç·/_,:;', 
        to  : 'aaaaaeeeeiiiiooooouuuunc------'
      };
 
      for (var i=0, j=map.from.length; i<j; i++) {
        slug = slug.replace(new RegExp(map.from.charAt(i), 'g'), map.to.charAt(i));
      }
      return slug.replace(strip, '').trim().replace(hyphen, '-');
    };
  });