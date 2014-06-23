/*
 * angular-elastic v2.3.2
 * (c) 2013 Monospaced http://monospaced.com
 * License: MIT
 */
angular.module('sven.D3', [])

  .factory('TimelineFactory',[ function() {
    var timeline = {};

    timeline.data = function(v){
      if (!arguments.length) return data;
      data = v;
      // update!!!
      return timeline;
    };

    timeline.init = function() {
      return timeline;
    };

    return timeline;
  }])

  .directive('d3Timeline', ['TimelineFactory', function(TimelineFactory) {
    return{
      restrict: 'A',
      scope: {
        inititalData: '=',
        data: '='
      },
      link: function(scope, element, attrs) {
        t = TimelineFactory.init();

        scope.$watch('data', function(){ // on data changes
          //scope.render(d3.values(scope.data))
          t.data(scope.data);  
          
        });
      }
    };
  }]);