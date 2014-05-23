'use strict';

/* Directives */


angular.module('sven.directives', [])
  .directive('scrollToFixed', function() {
    return{
      restrict: 'A',
      scope: {
        marginTop: '='
      },
      link: function (scope, element, attrs) {
        $(element).scrollToFixed({
          marginTop: scope.marginTop || 0
        });
      }
    };
  })
  .directive('appVersion', ['version', function(version) {
    return function(scope, elm, attrs) {
      elm.text(version);
    };
  }]);