/*
 * angular-wrappers.d3
 * (c) 2013 Monospaced http://monospaced.com
 * License: MIT
 */
'use strict';
angular.module('sven.D3', [])

  .factory('TimelineFactory',[ function() {
    var timeline = {}, 
        data,
        bounds, // width and height 
        x,
        y;

    timeline.parseDatetime = function(v) {

    };

    /*  
      data must be provided as an array of objects containing at least:
      {datetime: 1231331, value: 23.445}
    */ 
    timeline.data = function(v){ // getter setter
      if (!arguments.length) return data;
      data = v;
      // update xy domains!!!
      x.domain(d3.extent(data, function(d) { return d.datetime; }));
      y.domain(d3.extent(data, function(d) { return d.value; }));

      return timeline;
    };


    timeline.init = function(options) {
      options = options || {};
      timeline.bounds({
        width: options.width || 100,
        height: options.height || 200
      })
      return timeline;
    };


    timeline.bounds = function(v) {
      if (!arguments.length) return bounds;

      bounds = angular.extend({
        width: 0,
        height: 0
      }, v);

      x = d3.time.scale().range([0, bounds.width]);
      y = d3.time.scale().range([0, bounds.height]);
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
        var t = TimelineFactory.init();

        scope.$watch('data', function(){ // on data changes
          //scope.render(d3.values(scope.data))
          t.data(scope.data);  
          
        });
      }
    };
  }]);