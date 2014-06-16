/*
 * angular-elastic v2.3.2
 * (c) 2013 Monospaced http://monospaced.com
 * License: MIT
 */
angular.module('sven.D3', [])

  .factory('d3Factory', ['$document', '$q', '$rootScope',
    function($document, $q, $rootScope) {
      var d = $q.defer();
      function onScriptLoad() {
        // Load client in the browser
        $rootScope.$apply(function() { d.resolve(window.d3); });
      }
      // Create a script tag with d3 as the source
      // and call our onScriptLoad callback when it
      // has been loaded
      var scriptTag = $document[0].createElement('script');
      scriptTag.type = 'text/javascript'; 
      scriptTag.async = true;
      scriptTag.src = 'http://d3js.org/d3.v3.min.js';
      scriptTag.onreadystatechange = function () {
        if (this.readyState == 'complete') onScriptLoad();
      }
      scriptTag.onload = onScriptLoad;

      var s = $document[0].getElementsByTagName('body')[0];
      s.appendChild(scriptTag);

      return {
        d3: function() { return d.promise; }
      };
    }
  ])

  .directive('d3timeline', 'd3Factory', function(d3) {
    return{
      restrict: 'A',
      scope: {
        inititalData: '=',
        data: '='
      },
      link: function(scope, element, attrs) {
        d3Factory.d3().then(function(d3) { // when it has really been loaded

          scope.$watch('data', function(){ // on data changes
            //scope.render(d3.values(scope.data))
            debugger;
          });
        });
      }
    };
  });