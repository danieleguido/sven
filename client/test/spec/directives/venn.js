'use strict';

describe('Directive: venn', function () {

  // load the directive's module
  beforeEach(module('svenClientApp'));

  var element,
    scope;

  beforeEach(inject(function ($rootScope) {
    scope = $rootScope.$new();
  }));

  it('should make hidden element visible', inject(function ($compile) {
    element = angular.element('<venn></venn>');
    element = $compile(element)(scope);
    expect(element.text()).toBe('this is the venn directive');
  }));
});
